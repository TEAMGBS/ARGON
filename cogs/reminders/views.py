from __future__ import annotations

import discord

from database import reminders as reminders_db

from .constants import CLAN_ROLES, ROLE_LABELS, TIMING_CHOICES, TOWNHALL_LEVELS, TYPE_LABELS
from .state import ReminderState


class MessageModal(discord.ui.Modal, title="Edit Reminder Message"):
    text = discord.ui.TextInput(label="Message", style=discord.TextStyle.paragraph, max_length=500, required=False)

    def __init__(self, parent_view: "ReminderConfigView") -> None:
        super().__init__()
        self.parent_view = parent_view
        self.text.default = parent_view.state.message

    async def on_submit(self, interaction: discord.Interaction) -> None:
        self.parent_view.state.message = self.text.value
        self.parent_view.render()
        await interaction.response.edit_message(view=self.parent_view)


class ThresholdModal(discord.ui.Modal, title="Set Minimum Threshold"):
    text = discord.ui.TextInput(label="Minimum value", required=True, max_length=6)

    def __init__(self, parent_view: "ReminderConfigView") -> None:
        super().__init__()
        self.parent_view = parent_view
        self.text.default = str(parent_view.state.threshold)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if not self.text.value.isdigit():
            await interaction.response.send_message("Enter a whole number.", ephemeral=True)
            return
        self.parent_view.state.threshold = int(self.text.value)
        self.parent_view.render()
        await interaction.response.edit_message(view=self.parent_view)


class ReminderConfigView(discord.ui.LayoutView):
    def __init__(self, state: ReminderState) -> None:
        super().__init__(timeout=900)
        self.state = state
        self.render()

    def render(self) -> None:
        self.clear_items()
        container = discord.ui.Container()

        header = TYPE_LABELS[self.state.type]
        summary_lines = [f"**{header}**", f"Clan: {self.state.clan_name} ({self.state.clan_tag})"]
        if self.state.message:
            summary_lines.append(self.state.message)
        if self.state.reminder_id:
            summary_lines.append(f"ID: `{self.state.reminder_id}`")
        container.add_item(discord.ui.TextDisplay("\n".join(summary_lines)))
        container.add_item(discord.ui.Separator())

        timing_row = discord.ui.ActionRow()
        timing_select = discord.ui.Select(
            placeholder="Select reminder timing",
            min_values=1,
            max_values=len(TIMING_CHOICES),
            options=[
                discord.SelectOption(label=label, value=str(minutes), default=minutes in self.state.timing_minutes)
                for minutes, label in TIMING_CHOICES
            ],
        )
        timing_select.callback = self.on_timing_select
        timing_row.add_item(timing_select)
        container.add_item(timing_row)

        if self.state.type == "war":
            remaining_row = discord.ui.ActionRow()
            for value in (1, 2):
                button = discord.ui.Button(
                    label=f"{value} Remaining",
                    style=discord.ButtonStyle.primary
                    if value in self.state.remaining_filter
                    else discord.ButtonStyle.secondary,
                )
                button.callback = self.make_remaining_callback(value)
                remaining_row.add_item(button)
            container.add_item(remaining_row)
        else:
            threshold_row = discord.ui.ActionRow()
            unit = "minimum attacks" if self.state.type == "capital" else "minimum points"
            threshold_button = discord.ui.Button(
                label=f"{self.state.threshold} {unit}", style=discord.ButtonStyle.secondary
            )
            threshold_button.callback = self.on_threshold_button
            threshold_row.add_item(threshold_button)
            container.add_item(threshold_row)

        scope_row = discord.ui.ActionRow()
        all_button = discord.ui.Button(
            label="All Members",
            style=discord.ButtonStyle.primary if self.state.member_scope == "all" else discord.ButtonStyle.secondary,
        )
        all_button.callback = self.on_all_members
        scope_row.add_item(all_button)
        container.add_item(scope_row)

        th_row = discord.ui.ActionRow()
        th_select = discord.ui.Select(
            placeholder="Filter by Town Hall level",
            min_values=0,
            max_values=len(TOWNHALL_LEVELS),
            options=[
                discord.SelectOption(label=f"TH{level}", value=str(level), default=level in self.state.townhalls)
                for level in TOWNHALL_LEVELS
            ],
        )
        th_select.callback = self.on_th_select
        th_row.add_item(th_select)
        container.add_item(th_row)

        role_row = discord.ui.ActionRow()
        for role in CLAN_ROLES:
            button = discord.ui.Button(
                label=ROLE_LABELS[role],
                style=discord.ButtonStyle.primary if role in self.state.roles else discord.ButtonStyle.secondary,
            )
            button.callback = self.make_role_callback(role)
            role_row.add_item(button)
        container.add_item(role_row)

        action_row = discord.ui.ActionRow()
        edit_button = discord.ui.Button(label="Edit Reminder Message", style=discord.ButtonStyle.secondary)
        edit_button.callback = self.on_edit_message
        action_row.add_item(edit_button)
        save_button = discord.ui.Button(label="Save", style=discord.ButtonStyle.success)
        save_button.callback = self.on_save
        action_row.add_item(save_button)
        container.add_item(action_row)

        self.add_item(container)

    async def on_timing_select(self, interaction: discord.Interaction) -> None:
        values = interaction.data.get("values", [])
        self.state.timing_minutes = sorted(int(v) for v in values)
        self.render()
        await interaction.response.edit_message(view=self)

    def make_remaining_callback(self, value: int):
        async def callback(interaction: discord.Interaction) -> None:
            if value in self.state.remaining_filter:
                self.state.remaining_filter.remove(value)
            else:
                self.state.remaining_filter.append(value)
            self.render()
            await interaction.response.edit_message(view=self)

        return callback

    async def on_threshold_button(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_modal(ThresholdModal(self))

    async def on_all_members(self, interaction: discord.Interaction) -> None:
        self.state.member_scope = "all"
        self.state.townhalls = []
        self.state.roles = []
        self.render()
        await interaction.response.edit_message(view=self)

    async def on_th_select(self, interaction: discord.Interaction) -> None:
        values = interaction.data.get("values", [])
        self.state.townhalls = sorted(int(v) for v in values)
        self.state.member_scope = "filtered" if self.state.townhalls or self.state.roles else "all"
        self.render()
        await interaction.response.edit_message(view=self)

    def make_role_callback(self, role: str):
        async def callback(interaction: discord.Interaction) -> None:
            if role in self.state.roles:
                self.state.roles.remove(role)
            else:
                self.state.roles.append(role)
            self.state.member_scope = "filtered" if self.state.townhalls or self.state.roles else "all"
            self.render()
            await interaction.response.edit_message(view=self)

        return callback

    async def on_edit_message(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_modal(MessageModal(self))

    async def on_save(self, interaction: discord.Interaction) -> None:
        if not self.state.timing_minutes:
            await interaction.response.send_message("Select at least one reminder timing before saving.", ephemeral=True)
            return

        await interaction.response.defer()

        try:
            if not self.state.reminder_id:
                self.state.reminder_id = await reminders_db.create_reminder(
                    guild_id=self.state.guild_id,
                    clan_tag=self.state.clan_tag,
                    type_=self.state.type,
                    channel_id=self.state.channel_id,
                    created_by=self.state.created_by,
                    message=self.state.message,
                )

            await reminders_db.update_reminder(
                self.state.reminder_id,
                message=self.state.message,
                channel_id=self.state.channel_id,
                timing_minutes=self.state.timing_minutes,
                threshold=self.state.threshold,
                remaining_filter=self.state.remaining_filter,
                member_scope=self.state.member_scope,
                townhalls=self.state.townhalls,
                roles=self.state.roles,
            )
        except Exception as e:
            await interaction.followup.send(f"Failed to save reminder: {e}", ephemeral=True)
            return

        self.stop()
        for item in self.walk_children():
            if isinstance(item, discord.ui.Button):
                item.disabled = True
            if isinstance(item, discord.ui.Select):
                item.disabled = True
        await interaction.edit_original_response(view=self)
        await interaction.followup.send(f"Reminder saved. ID: `{self.state.reminder_id}`", ephemeral=True)
