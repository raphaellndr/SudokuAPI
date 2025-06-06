"""Game records choices."""

from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _

from app.core.choices import ExtendedTextChoicesMeta


class GameStatusChoices(TextChoices, metaclass=ExtendedTextChoicesMeta):
    """Game status choices."""

    IN_PROGRESS = "in_progress", _("In Progress")
    COMPLETED = "completed", _("Completed")
    ABANDONED = "abandoned", _("Abandoned")
    STOPPED = "stopped", _("Stopped")
