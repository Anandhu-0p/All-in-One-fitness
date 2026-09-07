from django.contrib.auth.models import Group

ROLE_ADMIN = 'Admin'
ROLE_TRAINER = 'Trainer'
ROLE_EXPERT = 'Expert'
ROLE_USER = 'User'

ROLE_CHOICES = [
    (ROLE_ADMIN, 'Administrator'),
    (ROLE_TRAINER, 'Trainer'),
    (ROLE_EXPERT, 'Expert'),
    (ROLE_USER, 'User'),
]


def get_or_create_groups():
    return {
        name: Group.objects.get_or_create(name=name)[0]
        for name in (ROLE_TRAINER, ROLE_EXPERT, ROLE_USER)
    }


def user_role(user):
    """Return the platform role label for a user."""
    if user is None:
        return None
    if user.is_superuser:
        return ROLE_ADMIN
    if user.groups.filter(name=ROLE_TRAINER).exists():
        return ROLE_TRAINER
    if user.groups.filter(name=ROLE_EXPERT).exists():
        return ROLE_EXPERT
    if user.groups.filter(name=ROLE_USER).exists():
        return ROLE_USER
    return ROLE_USER


def is_admin(user):
    return bool(user and user.is_superuser)


def is_trainer(user):
    return bool(user and user.groups.filter(name=ROLE_TRAINER).exists())


def is_expert(user):
    return bool(user and user.groups.filter(name=ROLE_EXPERT).exists())


def is_user(user):
    return bool(user and (user.groups.filter(name=ROLE_USER).exists() or not (is_trainer(user) or is_expert(user) or is_admin(user))))


def assign_role(user, role):
    """Replace a user's role groups with exactly one role."""
    user.groups.clear()
    if role and role != ROLE_ADMIN:
        group, _ = Group.objects.get_or_create(name=role)
        user.groups.add(group)
    if role == ROLE_ADMIN:
        user.is_staff = True
        user.is_superuser = True
    user.save()


def dashboard_url_for(user):
    role = user_role(user)
    if role == ROLE_ADMIN:
        return 'admin_dashboard'
    if role == ROLE_TRAINER:
        return 'trainer_dashboard'
    if role == ROLE_EXPERT:
        return 'expert_dashboard'
    return 'user_dashboard'