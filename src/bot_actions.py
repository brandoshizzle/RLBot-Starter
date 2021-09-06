from util.helpers import *
from rlbot.utils.structures.quick_chats import QuickChats


def bot_actions(
    self,
    packet,
    controls,
    car,
    ball,
    teammate,
    opponent_1,
    opponent_2,
    my_net,
    opponent_net,
):
    # By default we will chase the ball, but target_location can be changed later
    target_location = ball.location

    if car.distance_to(ball.location) > 1500:
        target_location = ball.location_at_seconds(1)
    else:
        target_location = ball.location_at_seconds(0.2)

    # flip if we're close
    if car.distance_to(ball.location) < 300:
        return front_flip(self, packet)

    if car.on_floor:
        controls.boost = True
    else:
        controls.boost = False

    if car.boost == 0 and car.distance_to(car.closest_boost.location) < 200:
        target_location = car.closest_boost.location

    controls.throttle = 1
    controls.steer = car.steer_towards(target_location)
    if ball.in_opponents_half:
        quick_chat = QuickChats.Information_Defending
        target_location = my_net.far_post
        controls.steer = car.steer_towards(target_location)
        if car.distance_to(target_location) < 400:
            controls = car.face_in_place(controls, opponent_1.location)
    else:
        target_location = ball.location

    if abs(car.angle_to(target_location)) > 60:
        controls.handbrake = True
    else:
        controls.handbrake = False

    controls.jump = False

    # Don't change this
    return controls, target_location, quick_chat
