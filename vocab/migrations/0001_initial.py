# -*- coding: utf-8 -*-
# Generated by Django 1.11.9 on 2018-01-30 13:37
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Alias',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, default=b'', help_text=b'alias name', max_length=1024)),
                ('termname', models.CharField(blank=True, default=b'', help_text=b'real term name', max_length=1024)),
            ],
        ),
        migrations.CreateModel(
            name='Phrase',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('regex', models.CharField(blank=True, default=b'', help_text=b'Regular expression to find text to replace', max_length=1024)),
                ('text', models.CharField(blank=True, default=b'', help_text=b'Text to replace in term description', max_length=4096)),
            ],
        ),
        migrations.CreateModel(
            name='Proposal',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateField(auto_now_add=True, help_text=b'Date when proposal was created was published.', null=True)),
                ('status', models.CharField(blank=True, choices=[(b'new', b'new'), (b'under discussion', b'under discussion'), (b'rejected', b'rejected'), (b'complete', b'complete'), (b'accepted', b'accepted')], default=b'New', help_text=b'Status of request', max_length=64)),
                ('proposer', models.CharField(blank=True, default=b'', help_text=b'name of proposer', max_length=1024)),
                ('proposed_date', models.DateField(blank=True, help_text=b'Date when proposal was first made.', null=True)),
                ('comment', models.TextField(blank=True, default=b'', help_text=b'comment on proposal', max_length=2048, null=True)),
                ('mail_list_url', models.URLField(blank=True, default=b'', help_text=b'URL of Mailing list thread', max_length=1024, null=True)),
                ('mail_list_title', models.CharField(blank=True, default=b'', help_text=b'title of mailing list thread', max_length=256, null=True)),
                ('alias', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='ProposedTerms',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('change_date', models.DateTimeField(auto_now_add=True, help_text=b'Date the term was last changed.')),
                ('proposal', models.ForeignKey(help_text=b'Link to Request that generated the term', on_delete=django.db.models.deletion.CASCADE, to='vocab.Proposal')),
            ],
        ),
        migrations.CreateModel(
            name='Term',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('externalid', models.CharField(blank=True, default=b'', help_text=b'machine readable id', max_length=256)),
                ('name', models.CharField(blank=True, default=b'', help_text=b'term text', max_length=1024)),
                ('description', models.CharField(blank=True, default=b'', help_text=b'description of term', max_length=4096)),
                ('unit', models.CharField(blank=True, default=b'', help_text=b'unit', max_length=256)),
                ('unit_ref', models.CharField(blank=True, default=b'', help_text=b'reference for unit', max_length=256)),
                ('amip', models.CharField(blank=True, default=b'', help_text=b'amip name/number for term', max_length=256)),
                ('grib', models.CharField(blank=True, default=b'', help_text=b'Grib name/number for term', max_length=256)),
            ],
        ),
        migrations.CreateModel(
            name='VocabList',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, default=b'', help_text=b'title of vocab', max_length=256)),
            ],
        ),
        migrations.CreateModel(
            name='VocabListVersion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('version', models.IntegerField(help_text=b'version number of vocab list')),
                ('published_date', models.DateField(auto_now_add=True, help_text=b'Date when list was published.')),
                ('status', models.CharField(blank=True, choices=[(b'Blank', b'Blank'), (b'copied', b'copied'), (b'Changed', b'Changed'), (b'Complete', b'Complete')], default=b'Blank', help_text=b'Status of list', max_length=64)),
                ('terms', models.ManyToManyField(blank=True, to='vocab.Term')),
                ('vocab_list', models.ForeignKey(blank=True, help_text=b'Vocab list for which this is a version', null=True, on_delete=django.db.models.deletion.CASCADE, to='vocab.VocabList')),
            ],
        ),
        migrations.AddField(
            model_name='proposedterms',
            name='term',
            field=models.ForeignKey(help_text=b'Link to the term', on_delete=django.db.models.deletion.CASCADE, to='vocab.Term'),
        ),
        migrations.AddField(
            model_name='proposal',
            name='terms',
            field=models.ManyToManyField(blank=True, through='vocab.ProposedTerms', to='vocab.Term'),
        ),
        migrations.AddField(
            model_name='proposal',
            name='vocab_list',
            field=models.ForeignKey(blank=True, help_text=b'If the proposal is accepted the term will be added to a version of this list.', null=True, on_delete=django.db.models.deletion.CASCADE, to='vocab.VocabList'),
        ),
        migrations.AddField(
            model_name='proposal',
            name='vocab_list_version',
            field=models.ForeignKey(blank=True, help_text=b'After it was accepted the term was added to this version of the list.', null=True, on_delete=django.db.models.deletion.CASCADE, to='vocab.VocabListVersion'),
        ),
    ]