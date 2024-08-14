from datetime import datetime, timedelta
from typing import Callable, overload

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
import pendulum

from app.models import UserEvent, UserAttribute
from app.schemas.campaign import (
    ScheduledDeliveryCampaign, ActionBasedDeliveryCampaign,
)

UserAction = UserEvent | UserAttribute
ScheduledDeliveryCallback = Callable[[ScheduledDeliveryCampaign], None]
ActionBasedDeliveryCallback = Callable[[ActionBasedDeliveryCampaign, UserAction], None]

timezone = "Asia/Seoul"


class ScheduleService:
    def __init__(self):
        scheduler = BackgroundScheduler(
            jobstores={
                "default": MemoryJobStore(),
            },
            executors={
                "default": ThreadPoolExecutor(10),
            },
            job_defaults={
                "coalesce": False,
                "max_instances": 3,
            },
        )
        scheduler.start()

        self._scheduler = scheduler

    def add_scheduled_delivery(
            self,
            callback: ScheduledDeliveryCallback,
            campaign: ScheduledDeliveryCampaign,
    ) -> None:
        schedule = campaign["schedule"]

        if schedule is None:
            trigger = None
        else:
            start_date, end_date = schedule["start_date"], schedule["end_date"]

            match schedule["frequency"]:
                case "once":
                    trigger = DateTrigger(run_date=schedule["start_date"], timezone=timezone)
                case "daily":
                    trigger = IntervalTrigger(
                        days=1,
                        start_date=start_date,
                        end_date=end_date,
                        timezone=timezone,
                    )
                case "weekly":
                    trigger = IntervalTrigger(
                        weeks=1,
                        start_date=start_date,
                        end_date=end_date,
                        timezone=timezone,
                    )
                case "monthly":
                    trigger = IntervalTrigger(
                        days=30,  # TODO: FIX
                        start_date=start_date,
                        end_date=end_date,
                        timezone=timezone,
                    )
                case _:
                    raise ValueError()

        job_id = self._job_id(campaign)
        self._scheduler.add_job(
            func=callback,
            trigger=trigger,
            args=[campaign],
            id=job_id,
        )

    def add_action_based_delivery(
            self,
            callback: ActionBasedDeliveryCallback,
            campaign: ActionBasedDeliveryCampaign,
            action: UserAction,
    ) -> None:
        now = pendulum.now(tz=timezone)

        match campaign["delay"]:
            case int() as delay:
                trigger = DateTrigger(run_date=(now + timedelta(seconds=delay)), timezone=timezone)
            case dict() as delay:
                if delay["op"] == "weekday":
                    at_date = now.next(day_of_week=delay["value"]).date()
                elif delay["op"] == "days":
                    at_date = now.add(days=delay["value"]).date()
                else:
                    raise ValueError()

                run_date = datetime.combine(at_date, delay["at_time"])
                trigger = DateTrigger(run_date, timezone=timezone)
            case _:
                trigger = None

        job_id = self._job_id(campaign, action)
        self._scheduler.add_job(
            func=callback,
            trigger=trigger,
            args=[campaign, action],
            id=job_id,
        )

    @overload
    def exists(self, campaign: ScheduledDeliveryCampaign) -> bool:
        ...

    @overload
    def exists(self, campaign: ActionBasedDeliveryCampaign, action: UserAction) -> bool:
        ...

    def exists(
            self,
            campaign: ScheduledDeliveryCampaign | ActionBasedDeliveryCampaign,
            action: UserAction | None = None,
    ) -> bool:
        job_id = self._job_id(campaign, action)
        return self._scheduler.get_job(job_id) is not None

    @overload
    def remove(self, campaign: ScheduledDeliveryCampaign) -> None:
        ...

    @overload
    def remove(self, campaign: ActionBasedDeliveryCampaign, action: UserAction) -> None:
        ...

    def remove(
            self,
            campaign: ScheduledDeliveryCampaign | ActionBasedDeliveryCampaign,
            action: UserAction | None = None,
    ) -> None:
        job_id = self._job_id(campaign, action)
        self._scheduler.remove_job(job_id)

    @staticmethod
    def _job_id(
            campaign: ScheduledDeliveryCampaign | ActionBasedDeliveryCampaign,
            action: UserAction | None = None,
    ):
        job_id = str(campaign["_id"])
        if action is not None:
            job_id = f"{job_id}:{action.user_id}"
        return job_id
