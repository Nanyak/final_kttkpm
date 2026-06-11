import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_id', models.IntegerField(unique=True)),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(default='')),
                ('category', models.CharField(default='', max_length=100)),
                ('price', models.FloatField(default=0.0)),
                ('encoded_id', models.IntegerField(blank=True, null=True)),
            ],
            options={'db_table': 'ai_products'},
        ),
        migrations.CreateModel(
            name='UserBehavior',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_id', models.IntegerField(db_index=True)),
                ('action', models.CharField(
                    choices=[
                        ('view', 'View'),
                        ('click', 'Click'),
                        ('add_to_cart', 'Add to Cart'),
                        ('purchase', 'Purchase'),
                    ],
                    max_length=20,
                )),
                ('timestamp', models.DateTimeField()),
                ('weight', models.FloatField(default=1.0)),
                ('product', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='behaviors',
                    to='behavior.product',
                    to_field='product_id',
                )),
            ],
            options={
                'db_table': 'ai_user_behavior',
                'ordering': ['user_id', 'timestamp'],
            },
        ),
        migrations.AddIndex(
            model_name='userbehavior',
            index=models.Index(fields=['user_id', 'timestamp'], name='ai_behavior_user_ts_idx'),
        ),
    ]
