from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.messages.flat.QuickChatSelection import QuickChatSelection
from rlbot.utils.structures.quick_chats import QuickChats
from rlbot.utils.structures.game_data_struct import GameTickPacket

from util.ball_prediction_analysis import find_slice_at_time
from util.boost_pad_tracker import BoostPadTracker
from util.sequence import Sequence, ControlStep
from util.vec import Vec3

from util.helpers import *
from bot_actions import *


class MyBot(BaseAgent):
    def __init__(self, name, team, index):
        super().__init__(name, team, index)
        self.active_sequence: Sequence = None
        self.boost_pad_tracker = BoostPadTracker()
        self.quick_chat = None

    def initialize_agent(self):
        # Set up information about the boost pads now that the game is active and the info is available
        self.boost_pad_tracker.initialize_boosts(self.get_field_info())

    def get_output(self, packet: GameTickPacket) -> SimpleControllerState:
        car = my_car(packet.game_cars[self.index], packet, self.boost_pad_tracker)
        ball = the_ball(
            packet,
            packet.game_cars[self.index].team,
            (self.get_ball_prediction_struct()),
        )
        teammate, opponent_1, opponent_2 = self.get_other_cars(packet.game_cars, packet)
        my_net = net(packet, self.team, "own")
        opponent_net = net(packet, self.team, "opponent")
        controls = SimpleControllerState()
        controls.throttle = 1

        # This is good to keep at the beginning of get_output. It will allow you to continue
        # any sequences that you may have started during a previous call to get_output.
        if self.active_sequence is not None and not self.active_sequence.done:
            controls = self.active_sequence.tick(packet)
            if controls is not None:
                return controls

        """
        PUT YOUR CODE BELOW THIS
        """

        controls, target_location, self.quick_chat = bot_actions(
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
        )

        if self.quick_chat is not None:
            self.send_quick_chat(QuickChats.CHAT_EVERYONE, self.quick_chat)

        """
        PUT YOUR CODE ABOVE THIS
        """
        # Ignore after this
        # Draw some things to help understand what the bot is thinking
        self.renderer.draw_line_3d(car.location, target_location, self.renderer.white())
        self.renderer.draw_string_3d(
            car.location,
            1,
            1,
            f"Thing: {car.angle_to(opponent_1.location):.1f}",
            self.renderer.white(),
        )
        self.renderer.draw_rect_3d(
            target_location, 8, 8, True, self.renderer.cyan(), centered=True
        )

        return controls

    def get_other_cars(self, cars, packet):
        teammate = None
        opponent_1 = None
        opponent_2 = None
        i = -1
        for car in cars:
            i = i + 1
            if car.name == "":
                break
            if i == self.index:
                continue
            if car.team == self.team:
                teammate = my_car(car, packet, self.boost_pad_tracker)
            else:
                if opponent_1 == None:
                    opponent_1 = my_car(car, packet, self.boost_pad_tracker)
                else:
                    opponent_2 = my_car(car, packet, self.boost_pad_tracker)

        return teammate, opponent_1, opponent_2
