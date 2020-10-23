from django.contrib.auth.models import User
from django.db import models


class Tag(models.Model):
    '''Tags used to label exercises. They are global and can be added by all
    users. They are only removed if all exercises with corresponding tags are
    removed.'''
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class YoutubeLink(models.Model):
    '''Youtube links used to represent tutorial videos for exercises. It is
    represented only by value for v key in URI querystring.'''
    querystring = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.querystring

    def url(self):
        '''Full url to youtube video.'''
        return f'https://www.youtube.com/watch?v={self.querystring}'


class Muscle(models.Model):
    ''''Muscle names used for graphical representation of muscle groups trained
    during the exercise. This table should be read only and contain rows
    corresponding to each muscle choice.'''

    MUSCLES = (
        ('cal', 'Calves'),
        ('qua', 'Quadriceps'),
        ('ham', 'Hamstrings'),
        ('glu', 'Gluteus'),
        ('lob', 'Lower back'),
        ('lat', 'Lats'),
        ('tra', 'Trapezius'),
        ('abs', 'Abdominals'),
        ('pec', 'Pectorals'),
        ('del', 'Deltoids'),
        ('tri', 'Triceps'),
        ('bic', 'Biceps'),
        ('for', 'Forearms')
    )

    name = models.CharField(max_length=3, choices=MUSCLES, unique=True)

    def __str__(self):
        return self.name

class Exercise(models.Model):
    '''Basic app entity used to represent single exercise.'''

    EXERCISE_KINDS = (
        ('rep', 'reps'),
        ('rew', 'reps x weight'),
        ('tim', 'time'),
        ('dis', 'distance'),
    )

    name = models.CharField(max_length=100)
    kind = models.CharField(max_length=3, choices=EXERCISE_KINDS)
    instructions = models.TextField(blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    forks_count = models.IntegerField(default=0)
    tags = models.ManyToManyField(Tag)
    tutorials = models.ManyToManyField(YoutubeLink)
    muscles = models.ManyToManyField(Muscle)

    class Meta:
        unique_together = [['name', 'owner']]

    def __str__(self):
        return self.name

    def can_be_forked(self, userId):
        '''Determine if user with userId already have any exercise with this 
        exercise name. In such case exercise cannot be forked.'''
        if Exercise.objects.filter(name=self.name, owner=userId):
            return False
        return True
