import datetime
import itertools

from django.core.management.base import BaseCommand
from django.core import serializers
from django.db import transaction

from coredata.models import Semester, CourseOffering, Member, Unit


def clear_config(objects):
    for o in objects:
        o.config = {}


class Command(BaseCommand):
    def handle(self, *args, **options):
        # fail the atomic transaction, just to be double sure none of the changes below get committed
        try:
            with transaction.atomic():
                self._handle(*args, **options)
                raise ValueError()
        except ValueError:
            pass

    def _handle(self, *args, **options):
        data = []
        the_past = datetime.date.today() - datetime.timedelta(days=365)

        semesters = Semester.objects.all()
        data.append(semesters)

        all_units = Unit.objects.all()
        # Get units in dependency order, so .parent is there when inserting
        units = [u for u in all_units if u.parent is None]
        last_len = 0
        while len(units) != last_len:
            last_len = len(units)
            units.extend([u for u in all_units if u.parent in units and u not in units])
        clear_config(units)
        data.append(units)

        offerings = CourseOffering.objects.filter(semester__start__gte=the_past).exclude(component="CAN").select_related('course')
        clear_config(offerings)

        courses = {o.course for o in offerings}
        data.append(courses)
        data.append(offerings)

        instructors = Member.objects.filter(offering__in=offerings, role='INST', added_reason='AUTO').select_related('person')
        clear_config(instructors)

        people = {m.person for m in instructors}
        clear_config(people)
        for i, p in enumerate(people):
            p.emplid = str(400000000 + i)
            p.title = 'M'
        data.append(people)
        data.append(instructors)

        print(serializers.serialize('json', itertools.chain(*data), indent=2))

