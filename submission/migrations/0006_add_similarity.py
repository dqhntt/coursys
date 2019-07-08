# Generated by Django 2.2.2 on 2019-06-29 16:20

import courselib.json_fields
import django.core.files.storage
from django.db import migrations, models
import django.db.models.deletion
import submission.models.base


class Migration(migrations.Migration):

    dependencies = [
        ('grades', '0005_on_delete'),
        ('submission', '0005_on_delete'),
    ]

    operations = [
        migrations.CreateModel(
            name='SimilarityResult',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('generator', models.CharField(choices=[('MOSS', 'MOSS')], help_text='tool that generated the similarity results', max_length=4)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('config', courselib.json_fields.JSONField(default=dict)),
                ('activity', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='grades.Activity')),
            ],
            options={
                'unique_together': {('activity', 'generator')},
            },
        ),
        migrations.CreateModel(
            name='SimilarityData',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(help_text='identifier used to find this file within the SimilarityResult', max_length=100)),
                ('file', models.FileField(blank=True, max_length=500, null=True, storage=django.core.files.storage.FileSystemStorage(base_url=None, location='submitted_files'), upload_to=submission.models.base.similarity_upload_path)),
                ('config', courselib.json_fields.JSONField(default=dict)),
                ('result', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='submission.SimilarityResult')),
                ('submission', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='submission.Submission')),
            ],
            options={
                'unique_together': {('result', 'label')},
            },
        ),
    ]