import os
from common.realtime import sec_since_boot
from enum import Enum
from maneuverplots import ManeuverPlot
from plant import Plant
import numpy as np


class Maneuver(object):
  def __init__(self, title, duration, **kwargs):
    # Was tempted to make a builder class
    self.distance_lead = kwargs.get("initial_distance_lead", 200.0)
    self.speed = kwargs.get("initial_speed", 0.0)
    self.lead_relevancy = kwargs.get("lead_relevancy", 0) 

    self.grade_values = kwargs.get("grade_values", [0.0, 0.0])
    self.grade_breakpoints = kwargs.get("grade_breakpoints", [0.0, duration])
    self.speed_lead_values = kwargs.get("speed_lead_values", [0.0, 0.0])
    self.speed_lead_breakpoints = kwargs.get("speed_lead_breakpoints", [0.0, duration])

    self.cruise_button_presses = kwargs.get("cruise_button_presses", [])

    self.duration = duration
    self.title = title

    self.frameIdx = 0  # added by Hasnat
    self.pathOffset = 0.0  # added by Hasnat
    self.lLane = -1.85  # added by Hasnat
    self.rLane = 1.85  # added by Hasnat
    self.dPath = 0.0  # added by Hasnat

  def evaluate(self, output_dir):

    '''Create files to record the outputs and alerts/hazards -- Hasnat'''
    out_file = output_dir + '/outputs.csv'
    hazard_file = output_dir + '/hazards.txt'
    alert_file = output_dir + '/alerts.txt'
    fault_file = output_dir + '/fault_times.txt'

    outfile = open(out_file, 'w')
    outfile.write('frameIdx, distance(m), speed(m/s), acceleration(m/s2), angle_steer, gas, brake, steer_torque, d_rel(m), v_rel(m/s), c_path(m)\n')

    hazardfile = open(hazard_file, 'w')
    hazardfile.write('*********Hazards generated in this test run**********\n')

    alertfile = open(alert_file, 'w')
    alertfile.write('*********Alerts generated in this test run**********\n')
    alertfile.close()

    faultfile = open(fault_file, 'w')
    faultfile.close()

    visionLane = 1  # use path model from matlab output
    angle_steer = 0.0
    prev_distance = 0.0
    prev_angle_steer = 0.0
    delta_lane = 0.0
    thetaFactor = 0.1067  # this value has been derived empirically

    if visionLane==1:
      visionFile = os.path.join(os.getcwd(),'laneData.dat')
      with open(visionFile, 'r') as visionfile:
        line = visionfile.readline()
        lanes = line.split(',')
        lanes = [float(i) for i in lanes]


    left_line = -1.85
    right_line = 1.85

    reportHazardH1 = True
    reportHazardH2 = True
    reportHazardH3 = True
    
    #lead_relevancy:HOOK#

    """runs the plant sim and returns (score, run_data)"""
    plant = Plant(
      lead_relevancy = self.lead_relevancy,
      speed = self.speed,
      distance_lead = self.distance_lead
    )

    last_live100 = None
    event_queue = sorted(self.cruise_button_presses, key=lambda a: a[1])[::-1]
    plot = ManeuverPlot(self.title)

    buttons_sorted = sorted(self.cruise_button_presses, key=lambda a: a[1])
    current_button = 0

    while plant.current_time() < self.duration:
      while buttons_sorted and plant.current_time() >= buttons_sorted[0][1]:
        current_button = buttons_sorted[0][0]
        buttons_sorted = buttons_sorted[1:]
        print "current button changed to", current_button
    
      grade = np.interp(plant.current_time(), self.grade_breakpoints, self.grade_values)
      speed_lead = np.interp(plant.current_time(), self.speed_lead_breakpoints, self.speed_lead_values)

      self.frameIdx = self.frameIdx + 1    # added by Hasnat

      distance, speed, acceleration, distance_lead, brake, gas, steer_torque, live100, angle_steer, reportHazardH1, reportHazardH2, reportHazardH3 = plant.step(reportHazardH1, reportHazardH2, reportHazardH3, outfile, hazardfile, speed_lead, current_button, grade, self.frameIdx, self.pathOffset, self.lLane, self.rLane, delta_lane) # angle_steer (return parameter), outfile, hazardfile, self.frameIdx, self.pathOffset, lLane, rLane added by Hasnat

      ### Incorrect/noisy camera input
      #visionFault:HOOK#


      ############ lateral change w.r.t. angle_steer
      delta_lane = (angle_steer-prev_angle_steer)/thetaFactor
      self.lLane -= delta_lane
      self.rLane -= delta_lane
      self.dPath += delta_lane

      if self.frameIdx % 10 == 0:
        self.lLane = left_line - self.dPath
        self.rLane = right_line - self.dPath
        #print self.frameIdx
        #print self.lLane
        #print self.rLane
        #print self.dPath

      ### Incorrect Process Model
      #md:HOOK#

      prev_angle_steer = angle_steer
      prev_distance = distance
      #print '+++++++++++++++++++++++++++'
      #print "leftLane: "+str(self.lLane)
      #print "rightLane: "+str(self.rLane)
      #print "angle_steer: "+str(angle_steer)
      #print "delta_lane: "+str(delta_lane)
      self.pathOffset = self.pathOffset + 0.001  #added by Hasnat for adding offset the path points

      ## TO DO - Fault inject: first correct path model till trigger, then inject a fault and follow the adjusted path model for couple of seconds, then again provide correct path model [remember to subtract 'delta_lane' from the corrected lane points, as delta_lane is the new center path of vehicle]

      #########################


      if live100:
        last_live100 = live100[-1]

      d_rel = distance_lead - distance if self.lead_relevancy else 200. 
      v_rel = speed_lead - speed if self.lead_relevancy else 0. 

      if last_live100:
        # print last_live100
        #develop plots
        plot.add_data(
          time=plant.current_time(),
          gas=gas, brake=brake, steer_torque=steer_torque,
          distance=distance, speed=speed, acceleration=acceleration,
          up_accel_cmd=last_live100.upAccelCmd, ui_accel_cmd=last_live100.uiAccelCmd,
          d_rel=d_rel, v_rel=v_rel, v_lead=speed_lead,
          v_target_lead=last_live100.vTargetLead, pid_speed=last_live100.vPid,
          cruise_speed=last_live100.vCruise,
          jerk_factor=last_live100.jerkFactor,
          a_target_min=last_live100.aTargetMin, a_target_max=last_live100.aTargetMax)

    print "maneuver end"

    outfile.close()
    alertfile.close()

    return (None, plot)


