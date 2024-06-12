#Service string passed in body of conditionals in function:
#move_forward
#move_backward
#move_right
#move_left

#modify the function to passinn the appropraite vector instruciton and 
#read eac eleent and apply condiotnal for eahc element in loop to #have srevi sned
#service string sent is conditonal o current listoftwist beng read

# strings to send to service
#might have to modify service tu take larger step/more deliberate 90 #deg angle turns (or 45 deg and change code?)
twist_instructions = ["stay", "turnLeft", "moveForward", "turnRight", "moveForward", "turnRight", "moveForward", "turnLeft", "moveForward", "stay"] #["stay", "turnLeft", "moveForward", "turnLeft", "moveForward", "turnLeft", "moveForward", "stay"]#["stay", "turnLeft", "moveForward", "turnLeft", "moveForward", "turnRight", "moveForward", "stay"]
repetition_numbers = [2,1,3,1,3,1,3,1,2,2]#[2, 1, 1, 1, 3, 1, 2, 2]#[2, 1, 1, 1, 3, 1, 2, 2]

#twist_instructions: basic movememnt; no metric
#reptition_number: associate movement to metric
#TODO: find how much angle/distace is convered in 1 metric unit of movement in real-life measurements

forward_instr = [instruction for instruction, repeat in zip(twist_instructions, repetition_numbers) for _ in range(repeat)]

backward_instr = forward_instr[::-1]
#turn around
backward_instr.insert(2,'turnLeft') 
backward_instr.insert(2,'turnLeft')

#negate all turnin backward_instr exctp last turn?

#1. change all turns
change = lambda turnX : ('turnRight' if turnX == 'turnLeft' else 'turnLeft')
backward_instr = [change(i) if i in ["turnLeft","turnRight"] else i for i in backward_instr]

#2. undo the change turn on the last turn in backward_instr (or first turn command in backward_instr[::-1])
last_turn_index = next(i for i, instruction in enumerate(backward_instr[::-1]) if instruction in ["turnLeft", "turnRight"])
backward_instr[-last_turn_index-1] = change(backward_instr[-last_turn_index-1])

print(f"forward_instr:\n {forward_instr}")
print()
print(f"backward_instr:\n {backward_instr}")

#TODO test with 3219 mock case from A to B and B to A
#S: "stay" (idle)
# w
#asd (orientation: w: facing up, s: facing down, a: face right; d: face left #- mvoements above are relative to robot
#     these are just where the robotis orietned in a global frame)

#From A to B:
#         d->->[B]SS
#         ^
#         |
#         ^
#         |
#         ^
#         |
#[A]sSSd->w
#twist_instructions = ["stay", "turnLeft", "moveForward", "turnLeft", #"moveForward", "turnRight", "moveForward", "stay"]
#repetition_numbers = [2, 1, 1, 1, 3, 1, 2, 2]

#forward_instr:
# ['stay', 'stay', 'turnLeft', 'moveForward', 'turnLeft', 'moveForward', #'moveForward', 'moveForward', 'turnRight', 'moveForward', #'moveForward', 'stay', 'stay']



#From B to A:
#         s<-<-awdSS[B]
#         |
#         v
#         |
 #        v
 #        |
 #        v
 #SS[A]s<-a


#backward_instr:
 #['stay', 'stay', 'turnRight', 'turnRight', 'moveForward', 'moveForward', #'turnLeft', 'moveForward', 'moveForward', 'moveForward', 'turnRight', #'moveForward', 'turnLeft', 'stay', 'stay']
