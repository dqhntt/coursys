# Generated by Django 2.2.22 on 2021-07-27 12:18

import django.core.files.storage
from django.db import migrations, models
import grad.models


class Migration(migrations.Migration):

    dependencies = [
        ('grad', '0011_on_delete'),
    ]

    operations = [
        migrations.AddField(
            model_name='scholarship',
            name='entrydate',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='externaldocument',
            name='file_attachment',
            field=models.FileField(max_length=500, storage=django.core.files.storage.FileSystemStorage(base_url=None, file_permissions_mode=384, location='submitted_files'), upload_to=grad.models.attachment_upload_to),
        ),
        migrations.AlterField(
            model_name='gradstatus',
            name='status',
            field=models.CharField(choices=[('INCO', 'Incomplete Application'), ('COMP', 'Complete Application'), ('INRE', 'Application In-Review'), ('HOLD', 'Hold Application'), ('OFFO', 'Offer Out'), ('REJE', 'Rejected Application'), ('DECL', 'Declined Offer'), ('EXPI', 'Expired Application'), ('CONF', 'Confirmed Acceptance'), ('CANC', 'Cancelled Acceptance'), ('ARIV', 'Arrived'), ('ACTI', 'Active'), ('PART', 'Part-Time'), ('LEAV', 'On-Leave'), ('WIDR', 'Withdrawn'), ('GRAD', 'Graduated'), ('NOND', 'Non-degree'), ('GONE', 'Gone'), ('ARSP', 'Completed Special'), ('TRIN', 'Transferred from another department'), ('TROU', 'Transferred to another department'), ('DELE', 'Deleted Record'), ('DEFR', 'Deferred'), ('GAPL', 'Applied for Graduation'), ('GAPR', 'Graduation Approved'), ('WAIT', 'Waitlisted')], max_length=4),
        ),
        migrations.AlterField(
            model_name='gradstudent',
            name='current_status',
            field=models.CharField(choices=[('INCO', 'Incomplete Application'), ('COMP', 'Complete Application'), ('INRE', 'Application In-Review'), ('HOLD', 'Hold Application'), ('OFFO', 'Offer Out'), ('REJE', 'Rejected Application'), ('DECL', 'Declined Offer'), ('EXPI', 'Expired Application'), ('CONF', 'Confirmed Acceptance'), ('CANC', 'Cancelled Acceptance'), ('ARIV', 'Arrived'), ('ACTI', 'Active'), ('PART', 'Part-Time'), ('LEAV', 'On-Leave'), ('WIDR', 'Withdrawn'), ('GRAD', 'Graduated'), ('NOND', 'Non-degree'), ('GONE', 'Gone'), ('ARSP', 'Completed Special'), ('TRIN', 'Transferred from another department'), ('TROU', 'Transferred to another department'), ('DELE', 'Deleted Record'), ('DEFR', 'Deferred'), ('GAPL', 'Applied for Graduation'), ('GAPR', 'Graduation Approved'), ('WAIT', 'Waitlisted')], db_index=True, help_text='Current student status', max_length=4, null=True),
        ),
        migrations.AlterField(
            model_name='supervisor',
            name='supervisor_type',
            field=models.CharField(choices=[('SEN', 'Senior Supervisor'), ('COS', 'Co-Supervisor'), ('COM', 'Supervisor'), ('CHA', 'Defence Chair'), ('EXT', 'External Examiner'), ('SFU', 'SFU Examiner'), ('POT', 'Potential Supervisor')], max_length=3),
        ),
    ]
