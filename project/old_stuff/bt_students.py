#!/usr/bin/env python3

import py_trees as pt, py_trees_ros as ptr, rospy
from behaviours_student import *
from reactive_sequence import RSequence
from std_srvs.srv import Empty, SetBool, SetBoolRequest 
from geometry_msgs.msg import Pose, PoseStamped
from object_recognition_msgs.msg import RecognizedObject
import time
from math import pi


class detect_cube(pt.behaviour.Behaviour):

    """
    It detects the Aruco cube and returns success after that.
    """
    

    def cb(self, msg):
        self.pose_pub.publish(msg)
        self.detected = True

    def __init__(self, name):

        rospy.loginfo("Initialising detect_cube behaviour.")

        self.pose_sub = rospy.Subscriber('/robotics_intro/aruco_single/pose', PoseStamped, self.cb)
        self.pose_pub = rospy.Publisher('/marker_pose_topic', PoseStamped, queue_size=10)

        # execution checker
        self.detected = False

        # become a behaviour
        super(detect_cube, self).__init__(name)

    def update(self):

        # success if done
        if self.detected:
            return pt.common.Status.SUCCESS
        
        return pt.common.Status.FAILURE
    

class detect_cube_final(pt.behaviour.Behaviour):

    """
    It detects the Aruco cube and returns success after that.
    """

    DETECTION_MARGIN = 1000
    
    def cb(self, msg):
        if not self.first:
            self.detected = True
        
    def __init__(self, name):

        rospy.loginfo("Initialising detect_cube behaviour.")

        self.pose_sub = rospy.Subscriber('/robotics_intro/aruco_single/pose', PoseStamped, self.cb)

        # execution checker
        self.detected = False
        self.first = True

        # become a behaviour
        super(detect_cube_final, self).__init__(name)

    def update(self):
        if self.first:
            self.n = self.DETECTION_MARGIN
            self.first = False
            return pt.common.Status.RUNNING
             
        # success if done
        if self.detected:
            self.detected = False
            self.n = self.DETECTION_MARGIN
            return pt.common.Status.SUCCESS
        
        self.n -= 1

        if self.n > 0:
            return pt.common.Status.RUNNING
        
        return pt.common.Status.FAILURE


class pick_cube(pt.behaviour.Behaviour):
    """
    It picks the Aruco cube and returns success after that.
    """
    

    def __init__(self, name):

        rospy.loginfo("Initialising pick_cube behaviour.")
        
        self.pick_srv_name = rospy.get_param(rospy.get_name() + '/pick_srv')
        rospy.wait_for_service(self.pick_srv_name, timeout=30)
        self.pick_srv = rospy.ServiceProxy(self.pick_srv_name, SetBool)


        # execution checker
        self.tried = False
        self.done = False

        # become a behaviour
        super(pick_cube, self).__init__(name)

    def update(self):
        # success if done
        if self.done:
            return pt.common.Status.SUCCESS

        # try if not tried
        elif not self.tried:

            # command
            self.pick_req = self.pick_srv()
            self.tried = True

            # tell the tree you're running
            return pt.common.Status.RUNNING

        # if succesful
        elif self.pick_req.success:
            self.done = True
            return pt.common.Status.SUCCESS

        # if failed
        elif not self.pick_req.success:
            return pt.common.Status.FAILURE

        # if still trying
        return pt.common.Status.RUNNING

    
class go_to_table(pt.behaviour.Behaviour):
    def __init__(self, name):

        rospy.loginfo("Initialising go_to_table behaviour.")

        self.cmd_vel_top = rospy.get_param(rospy.get_name() + '/cmd_vel_topic')
        self.pub = rospy.Publisher(self.cmd_vel_top, Twist, queue_size=10)

        self.done = False

        # become a behaviour
        super(go_to_table, self).__init__(name)

    def update(self):
        rate = rospy.Rate(10)

        def send_twist_with_duration(twist, duration):
            start_time = time.time()

            while time.time() - start_time < duration:
                self.pub.publish(twist)
                rate.sleep()

        if self.done:
            return pt.common.Status.SUCCESS

        twist = Twist()
        twist.angular.z = pi/2
        send_twist_with_duration(twist, 2)

        self.pub.publish(Twist())
        rate.sleep()

        twist = Twist()
        twist.linear.x = 0.5
        send_twist_with_duration(twist, 2)

        self.pub.publish(Twist())
        self.done = True
        
        return pt.common.Status.SUCCESS


class place_cube(pt.behaviour.Behaviour):
    """
    It places the Aruco cube and returns success after that.
    """
    

    def __init__(self, name):

        rospy.loginfo("Initialising place_cube behaviour.")
        
        self.place_srv_name = rospy.get_param(rospy.get_name() + '/place_srv')
        rospy.wait_for_service(self.place_srv_name, timeout=30)
        self.place_srv = rospy.ServiceProxy(self.place_srv_name, SetBool)


        # execution checker
        self.tried = False
        self.done = False

        # become a behaviour
        super(place_cube, self).__init__(name)

    def update(self):
        # success if done
        if self.done:
            return pt.common.Status.SUCCESS

        # try if not tried
        elif not self.tried:

            # command
            self.place_req = self.place_srv()
            self.tried = True

            # tell the tree you're running
            return pt.common.Status.RUNNING

        # if succesful
        elif self.place_req.success:
            self.done = True
            return pt.common.Status.SUCCESS

        # if failed
        elif not self.place_req.success:
            return pt.common.Status.FAILURE

        # if still trying
        return pt.common.Status.RUNNING


class BehaviourTree(ptr.trees.BehaviourTree):

    def __init__(self):

        rospy.loginfo("Initialising behaviour tree")

        b0 = pt.composites.Selector(
            name="Detect cube fallback",
            children=[detect_cube("Detect the cube"), movehead("down")]
        )

        b1 = pt.composites.Selector(
            name="Pick cube fallback",
            children=[pick_cube("Pick the cube")]
        )

        b2 = pt.composites.Selector(
            name="Transport the cube to table B",
            children=[go_to_table("Go to point B")]
        )

        b3 = pt.composites.Selector(
            name="Place the cube on table B",
            children=[place_cube("Place cube on B")]
        )

        b4 = pt.composites.Selector(
            name="Check if cube is correctly placed",
            children=[ detect_cube_final("Check the cube again"), go_to_table("Go to point A")]
        )

    
        tree = RSequence(name="Main sequence", children=[b0, b1, b2, b3, b4])
        super(BehaviourTree, self).__init__(tree)

        # execute the behaviour tree
        rospy.sleep(5)
        self.setup(timeout=10000)
        while not rospy.is_shutdown(): self.tick_tock(1)	

if __name__ == "__main__":


    rospy.init_node('main_state_machine')
    try:
        BehaviourTree()
    except rospy.ROSInterruptException:
        pass

    rospy.spin()
