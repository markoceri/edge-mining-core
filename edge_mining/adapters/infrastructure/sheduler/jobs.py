from apscheduler.schedulers.asyncio import AsyncIOScheduler

from edge_mining.shared.scheduler.port import SchedulerPort
from edge_mining.shared.logging.port import LoggerPort
from edge_mining.application.services.mining_orchestrator import MiningOrchestratorService
from edge_mining.shared.settings.settings import AppSettings

class AutomationScheduler(SchedulerPort):
    def __init__(
        self,
        orchestrator: MiningOrchestratorService,
        logger: LoggerPort,
        settings: AppSettings
    ):
        self.orchestrator = orchestrator
        self.logger = logger
        self.settings = settings
        self.scheduler = AsyncIOScheduler(timezone=self.settings.timezome)
        
        self._job_id = "evaluate_mining"

    def _run_evaluation_job(self):
        """Wrapper to call the orchestrator's evaluation method."""
        self.logger.info(f"Scheduler triggered. Running job: {self._job_id}.")
        try:
            self.orchestrator.evaluate_and_control_miners()
        except Exception as e:
            self.logger.error(f"Error during scheduled job: {self._job_id}. {e}")
            # Consider sending a critical notification here

    async def start(self):
        """Adds the job and starts the scheduler."""
        interval = self.settings.scheduler_interval_seconds
        self.logger.info(f"Starting scheduler. job |{self._job_id}| will run every {interval} seconds.")

        self.scheduler.add_job(
            self._run_evaluation_job,
            'interval',
            seconds=interval,
            id=self._job_id,
            replace_existing=True
        )

        self.logger.info("Scheduler started.")
        self.scheduler.start()

    def stop(self):
        self.logger.info(f"Scheduler stopped. Job: {self._job_id}")
        self.scheduler.shutdown()