import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from ai.provider import AIProviderError, CLOUD_PROVIDERS, suggest_task_details


KEYS = {
    "gemini": "GEMINI_API_KEY",
    "openai": "OPENAI_API_KEY",
    "claude": "ANTHROPIC_API_KEY",
}
MODELS = {
    "gemini": ("GEMINI_MODEL", "gemini-2.5-flash"),
    "openai": ("OPENAI_MODEL", "provider default"),
    "claude": ("CLAUDE_MODEL", "provider default"),
}


class Command(BaseCommand):
    help = "Check Mawj's active AI configuration without printing API keys."

    def add_arguments(self, parser):
        parser.add_argument(
            "--live",
            action="store_true",
            help="Send a fixed, non-private test phrase to the configured cloud provider.",
        )

    def handle(self, *args, **options):
        provider = settings.AI_PROVIDER
        self.stdout.write(f"Active provider: {provider}")
        if provider not in CLOUD_PROVIDERS:
            self.stdout.write(
                self.style.WARNING(
                    "Live AI is not selected. Set AI_PROVIDER=gemini (or another cloud provider), "
                    "remove any conflicting terminal environment variable, and restart Django."
                )
            )
            return

        key_name = KEYS[provider]
        has_key = bool(os.environ.get(key_name, "").strip())
        model_name, model_default = MODELS[provider]
        model = os.environ.get(model_name, model_default)
        self.stdout.write(f"Model: {model}")
        self.stdout.write(f"{key_name}: {'configured' if has_key else 'missing'}")
        if not has_key:
            raise CommandError(f"Add {key_name} to the private .env file and restart Django.")
        if not options["live"]:
            self.stdout.write(self.style.SUCCESS("Configuration was loaded. Use --live to test the provider connection."))
            return

        try:
            suggest_task_details("Mawj connection test", "Return a small estimate for this fictional test.")
        except AIProviderError as error:
            raise CommandError(f"Provider check failed: {error}") from error
        self.stdout.write(self.style.SUCCESS("Provider connection succeeded. No journal text was sent."))
