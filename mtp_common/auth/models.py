class MojUser:
    """
    Authenticated user, similar to the Django one.

    The built-in Django `AbstractBaseUser` sadly depends on a few tables and
    cannot be used without a datbase so we had to create a custom one.
    """

    def __init__(self, pk, token, user_data):
        self.pk = pk
        self.is_active = True

        self.token = token
        self.user_data = user_data

    def save(self, *args, **kwargs):
        pass

    def is_anonymous(self):
        return False

    def is_authenticated(self, *args, **kwargs):
        return True

    def get_all_permissions(self, obj=None):
        return self.user_data.get('permissions', [])

    def has_perm(self, perm, obj=None):
        return perm in self.user_data.get('permissions', [])

    def has_perms(self, perm_list, obj=None):
        return all(
            [perm in self.user_data.get('permissions', []) for perm in perm_list]
        )

    @property
    def username(self):
        return self.user_data.get('username')

    @property
    def email(self):
        return self.user_data.get('email')

    def get_full_name(self):
        if not hasattr(self, '_full_name'):
            name_parts = [
                self.user_data.get('first_name'),
                self.user_data.get('last_name')
            ]
            self._full_name = ' '.join(filter(None, name_parts))
        return self._full_name


class MojAnonymousUser:
    """
    Anonymous non-authenticated user, similar to the Django one.

    The built-in Django `AnonymousUser` sadly depends on a few tables and
    gives several warnings when used without a database so we had to create a
    custom one.
    """
    pk = None
    is_active = False
    token = None
    user_data = {}
    username = ''
    email = ''

    def get_full_name(self):
        return ''

    def is_anonymous(self):
        return True

    def is_authenticated(self, *args, **kwargs):
        return False

    def get_all_permissions(self, obj=None):
        return []

    def has_perm(self, perm, obj=None):
        return False

    def has_perms(self, perm_list, obj=None):
        return False
