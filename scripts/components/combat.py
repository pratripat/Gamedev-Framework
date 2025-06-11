class WeaponComponent:
    def __init__(self, cooldown, shoot_fn, projectile_data):
        self.cooldown = cooldown
        self.shoot_fn = shoot_fn
        self.projectile_data = projectile_data

        self.time = 0
        self.shot = False

    @property
    def can_shoot(self):
        return not self.shot
