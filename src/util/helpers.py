import math
from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.messages.flat.QuickChatSelection import QuickChatSelection
from rlbot.utils.structures.game_data_struct import GameTickPacket
from util.orientation import Orientation, relative_location
from util.ball_prediction_analysis import find_slice_at_time
from util.boost_pad_tracker import BoostPadTracker
from util.drive import steer_toward_target
from util.sequence import Sequence, ControlStep
from util.vec import Vec3


class my_car:
    def __init__(self, car, packet, boost_pad_tracker):
        self.car = car
        self.packet = packet
        self.boost_pad_tracker = boost_pad_tracker
        self.previousThrottle = 1

        # Location
        self.location = Vec3(car.physics.location)
        # Velocity
        self.velocity = Vec3(car.physics.velocity)
        # Speed
        self.speed = self.velocity.length()
        # Pitch
        self.pitch = car.physics.rotation.pitch
        # Roll
        self.roll = car.physics.rotation.roll
        # Boost level
        self.boost = car.boost
        # Touching floor
        self.on_floor = True if self.location.z < 20 else False
        # Wheels on surface
        self.wheels_touching = car.has_wheel_contact
        # In own half
        self.in_own_half = (
            True
            if (car.team == 0 and self.location.y <= 0)
            or (car.team == 1 and self.location.y >= 0)
            else False
        )
        # Closest boosts
        self.closest_big_boost = self.get_big_boost()
        self.closest_boost = self.get_closest_boost()

    def distance_to(self, target_location):
        return self.location.dist(target_location)

    def angle_to(self, target_location):
        relative = relative_location(
            Vec3(self.car.physics.location),
            Orientation(self.car.physics.rotation),
            target_location,
        )
        angle = math.atan2(relative.y, relative.x)
        return angle * 180 / math.pi

    def steer_towards(self, target_location):
        return steer_toward_target(self.car, target_location)

    def get_big_boost(self):
        self.boost_pad_tracker.update_boost_status(self.packet)
        boost_list = self.boost_pad_tracker.get_full_boosts()
        closest_boost = None
        closest_distance = 1000000000
        for pad in boost_list:
            if pad.is_active == False:
                continue
            dist = self.location.dist(pad.location)
            if dist < closest_distance:
                closest_boost = pad
                closest_distance = dist
        return closest_boost

    def get_closest_boost(self):
        self.boost_pad_tracker.update_boost_status(self.packet)
        boost_list = self.boost_pad_tracker.boost_pads
        closest_boost = None
        closest_distance = 1000000000
        for pad in boost_list:
            if pad.is_active == False:
                continue
            dist = self.location.dist(pad.location)
            if dist < closest_distance:
                closest_boost = pad
                closest_distance = dist
        return closest_boost

    def face_in_place(self, controls, target_location):

        if abs(self.angle_to(target_location)) > 5:
            controls.handbrake = False
            controls.throttle = self.previousThrottle / abs(self.previousThrottle)
            if self.previousThrottle > 0:
                controls.steer = self.steer_towards(target_location)
                self.previousThrottle += 1
                if self.previousThrottle > 30:
                    self.previousThrottle = -1
            else:
                controls.steer = -self.steer_towards(target_location)
                self.previousThrottle -= 1
                if self.previousThrottle < -30:
                    self.previousThrottle = 1
        else:
            controls.throttle = 0

        return controls


class the_ball:
    def __init__(self, packet, team, ball_prediction):
        self.packet = packet
        self.ball = packet.game_ball
        self.ball_prediction = ball_prediction
        self.team = team

        # Location
        self.location = Vec3(self.ball.physics.location)
        # Velocity
        self.velocity = Vec3(self.ball.physics.velocity)
        # Speed
        self.speed = self.velocity.length()
        # Height
        self.height = self.location.z
        # In own half
        self.in_own_half = (
            True
            if (team == 0 and self.location.y <= 0)
            or (team == 1 and self.location.y >= 0)
            else False
        )
        self.in_opponents_half = not self.in_own_half
        # Going toward own net
        self.going_toward_own_net = (
            True
            if (team == 0 and self.velocity.y <= 0)
            or (team == 1 and self.velocity.y >= 0)
            else False
        )
        self.going_toward_opponents_net = not self.going_toward_own_net

    # Location at seconds
    def location_at_seconds(self, time):
        ball_in_future = find_slice_at_time(
            self.ball_prediction, self.packet.game_info.seconds_elapsed + time
        )

        # ball_in_future might be None if we don't have an adequate ball prediction right now, like during
        # replays, so check it to avoid errors.
        if ball_in_future is not None:
            return Vec3(ball_in_future.physics.location)
        else:
            return Vec3(0, 0, 0)


class net:
    def __init__(self, packet, team, which_net):
        self.packet = packet
        self.ball_location = packet.game_ball.physics.location
        self.ball_sign = 1 if self.ball_location.x > 0 else -1
        self.team = team
        self.which_net = which_net
        self.team_sign = (
            1
            if (team == 1 and which_net == "own")
            or (team == 0 and which_net == "opponent")
            else -1
        )
        self.location = Vec3(0, self.team_sign * 5120, 0)
        self.middle = Vec3(0, self.team_sign * 5120, 0)
        self.near_post = Vec3(self.ball_sign * 870, self.team_sign * 5120, 0)
        self.far_post = Vec3(self.ball_sign * -870, self.team_sign * 5120, 0)


def front_flip(self, packet):
    # Send some quickchat just for fun
    self.send_quick_chat(
        team_only=False, quick_chat=QuickChatSelection.Information_IGotIt
    )

    # Do a front flip. We will be committed to this for a few seconds and the bot will ignore other
    # logic during that time because we are setting the active_sequence.
    self.active_sequence = Sequence(
        [
            ControlStep(duration=0.05, controls=SimpleControllerState(jump=True)),
            ControlStep(duration=0.05, controls=SimpleControllerState(jump=False)),
            ControlStep(
                duration=0.2, controls=SimpleControllerState(jump=True, pitch=-1)
            ),
            ControlStep(duration=0.8, controls=SimpleControllerState()),
        ]
    )

    # Return the controls associated with the beginning of the sequence so we can start right away.
    return self.active_sequence.tick(packet)
