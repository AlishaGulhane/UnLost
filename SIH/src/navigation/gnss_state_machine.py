class GNSSStateMachine:
    def __init__(self):
        self.state = "available"
        self.lost_time = 0.0

    def update(self, gnss_available, dt):
        if gnss_available:
            self.state = "available"
            self.lost_time = 0.0
        else:
            self.lost_time += dt
            if self.lost_time < 5.0:
                self.state = "degraded"
            else:
                self.state = "dead_reckoning"
        return self.state
