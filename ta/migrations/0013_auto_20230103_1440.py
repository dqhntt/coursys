# Generated by Django 3.2.15 on 2023-01-03 14:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('coredata', '0025_update_choices'),
        ('ta', '0012_add_program_comment'),
    ]

    operations = [
        migrations.AddField(
            model_name='taapplication',
            name='supervisor',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='tasupervisor', to='coredata.person', verbose_name='If you are CS grad student, please identify your supervisor'),
        ),
        migrations.AlterField(
            model_name='taapplication',
            name='category',
            field=models.CharField(choices=[('GTA1', 'Masters'), ('GTA2', 'PhD'), ('UTA', 'Undergrad'), ('ETA', 'External')], help_text='What category of program are you currently studying?', max_length=4, verbose_name='Category'),
        ),
        migrations.AlterField(
            model_name='taapplication',
            name='current_program',
            field=models.CharField(blank=True, choices=[('CMPT', 'CMPT student'), ('OTHR', 'Other program'), ('NONS', 'Not currently a student')], help_text='In what department are you currently a student?', max_length=100, null=True, verbose_name='Current program'),
        ),
    ]
