we are using promicro nrf52840 board and we want use bmi160 to build a level for knife sharpening with a oled display and a calibration button:
config file for setting pins: 
104 goes sda on bmi160,
106 goes to scl on bmi160,
006 goes to sda on display
008 goes to sck on display
600 goes to goes to calibration button

the oled display is 0.91 inch
we want to implement code as a state machine: stages: init -> ready -> calibration
init: checks displays, checks bmi connection, transitions to ready
in ready the display displays the roll value
on press of the calibration button we enter calibration state: roll angle is displayed along with an indicator that we are in calibration; when the user presses the calibration button, the current roll angle is saved as the required angle. when they press the button long, we transition to ready state
in ready if the required angle is set then whenever the current roll angle deviates by more than 2 degrees, the display inverts colors.

make sure the displayed angle values are as big as possible

now we need to add a complementary filter that will keep the correct current angle value even when in rapid sharpening motion: this includes rapid back at forth movement with drastic stop at the end of each move.