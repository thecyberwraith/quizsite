# Generated by Django 4.0.5 on 2022-06-08 16:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CategoryModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
            ],
            options={
                'ordering': ['quiz', 'name'],
            },
        ),
        migrations.CreateModel(
            name='QuizModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name_plural': 'quizzes',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='QuestionModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.PositiveIntegerField()),
                ('question_text', models.TextField()),
                ('solution_text', models.TextField()),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='quiz.categorymodel')),
            ],
            options={
                'ordering': ['category', 'value'],
            },
        ),
        migrations.AddField(
            model_name='categorymodel',
            name='quiz',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='categories', to='quiz.quizmodel'),
        ),
    ]
