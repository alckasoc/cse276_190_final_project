########
# Name: sample_controller
#
# Purpose: A sample Pupper controller. Will move the robot around a bit then stop.
#
# Author: Prof. Riek <lriek@ucsd.edu>
#
# Date: 30 April 2024
#
# Prof. Riek Notes: Feel free to use this as starter code for the rest of the lab.
#####################

# Our custom interface, GoPupper. This specifies the message type (commands).
from pupper_interfaces.srv import GoPupper

# Packages to let us create nodes and spin them up
import rclpy
from rclpy.node import Node

###
# Method: Sample Controller Async
# Purpose: Constructor for the controler
#
######
class SampleControllerAsync(Node):

    def __init__(self):
        # initalize
        super().__init__('sample_controller')
        self.cli = self.create_client(GoPupper, 'pup_command')

        # Check once per second if service matching the name is available 
        while not self.cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('service not available, waiting again...')

        # Create a new request object.
        self.req = GoPupper.Request()


    ###
    # Name: send_move_request
    # Purpose: send_move_request method, send request and spin until receive response or fail
    # Arguments:  self (reference the current class), move_command (the command we plan to send to the server)
    #####
    def send_move_request(self, move_command):
        self.req = GoPupper.Request()
        self.req.command = move_command
        # Debug - uncomment if needed
        print("In send_move_request, command is: %s" % self.req.command)
        self.future = self.cli.call_async(self.req)  # send the command to the server
        rclpy.spin_until_future_complete(self, self.future)
        return self.future.result()

    ###
    # Name: pupper_conga_dance
    # Purpose: Try to make the robot do the Conga (salsa), as per Gloria Estefan. We don't
    #          have a robot choreopgraher here so we'll just do our best.
    # Arguments:  self (reference the current class) -- /not sure if needed, but won't hurt/
    #####
    #moveTo3219 = [] # turn_{left,right} #move_{forward,backward,left,right} #stay
    #for i in :moveTo3219:
        #self.send_move_request("move_"+)
    def pupper_conga_dance(self):
        # go left a few times
        for i in range(2):
            self.send_move_request("move_left")

        # go right a few times
        for i in range(2):
            self.send_move_request("move_right")

        # go backward 
        for i in range(3):
            self.send_move_request("move_backward")

        # go forward
        for i in range(3):
            self.send_move_request("move_forward")
###
# Name: Main
# Purpose: Main function. Going to try to have the robot dance salsa. 
#####
def main():
    rclpy.init()
    sample_controller = SampleControllerAsync()

    # send commands to do the conga dance
    sample_controller.pupper_conga_dance()

    # This spins up a client node, checks if it's done, throws an exception of there's an issue
    # (Probably a bit redundant with other code and can be simplified. But right now it works, so ¯\_(ツ)_/¯)
    while rclpy.ok():
        rclpy.spin_once(sample_controller)
        if sample_controller.future.done():
            try:
                response = sample_controller.future.result()
            except Exception as e:
                sample_controller.get_logger().info(
                    'Service call failed %r' % (e,))
            else:
                sample_controller.get_logger().info(
                   'Result of command: %s ' %
                   (response))
            break

    # Destroy node and shut down
    sample_controller.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()


