#include <AccelStepper.h>

#define PI 3.1415926535897932384626433832795

const int Step1 = 2;
const int Dir1 = 5;
const int Step2 = 3;
const int Dir2 = 6;
const int Step3 = 4;
const int Dir3 = 7;
const int StepW = 52;
const int DirW = 53;
const int ENA = 8;

const int limit1 = 21;
const int limit2 = 20;
const int limit3 = 19;
const int limitW = 18;

const int gripper = 51;

const float step123 = 5000;
const float degree123W = 360;
const float stepW = 1036;
const float offsetcam = 40;

int homing_complete = 0;
int done1 = 0;
int done2 = 0;
int done3 = 0;
int doneW = 0;

AccelStepper Motor1(1, Step1, Dir1);
AccelStepper Motor2(1, Step2, Dir2);
AccelStepper Motor3(1, Step3, Dir3);
AccelStepper MotorW(1, StepW, DirW); 

float theta1, theta2, theta3, thetaW;
int pt1, pt2, pt3, ptw;
int siklus;
float x, y, z, w;
float curr_x, curr_y, curr_z, curr_w;

//variable rahasia robot delta
double rb = 225; //jari jari base
double rp = 80; //jari jari platform
double lb = 230; //lengan ke base
double lp = 450; //lengan ke platform
double limitatas = -15;
double limitbawah = 80;
double theta[3];
double r[3];
double psi[3];
double Giri[3];
double hasilth[3];
int f1 = 0;


void setup() {

  Motor1.setMaxSpeed(400);
  Motor2.setMaxSpeed(400);
  Motor3.setMaxSpeed(400);
  MotorW.setMaxSpeed(300);
  Motor1.setAcceleration(200);
  Motor2.setAcceleration(200);
  Motor3.setAcceleration(200);
  MotorW.setAcceleration(100);
  
  pinMode(ENA, OUTPUT); 

  pinMode(limit1, INPUT_PULLUP);
  pinMode(limit2, INPUT_PULLUP);
  pinMode(limit3, INPUT_PULLUP);
  pinMode(limitW, INPUT_PULLUP);
  
  pinMode(gripper, OUTPUT);

  digitalWrite(ENA, 0);

  digitalWrite(gripper, 1);
  
  Serial.begin(9600);
}


int homing(){
  homing_complete = 0;
  done1 = 0;
  done2 = 0;
  done3 = 0;
  doneW = 0;
  while(homing_complete == 0) {
   if (digitalRead(limit1)) {
       Motor1.moveTo(-9999);
       Motor1.run(); 
   }
   else {
       done1 = 1;
   }

   if (digitalRead(limit2)) {
       Motor2.moveTo(-9999);
       Motor2.run(); 
   }
   else {
       done2 = 1;
   }

   if (digitalRead(limit3)) {
       Motor3.moveTo(-9999);
       Motor3.run(); 
   }
   else {
       done3 = 1;
   }
 
   if (done1 == 1 and done2 == 1 and done3 == 1) {
      homing_complete = 1;
      Motor1.setCurrentPosition(0);
      Motor2.setCurrentPosition(0);
      Motor3.setCurrentPosition(0);
      break;
   }
}

  while(homing_complete == 1) {
    Motor1.moveTo(100);
    Motor2.moveTo(100);
    Motor3.moveTo(100);
    Motor1.run();
    Motor2.run();
    Motor3.run();

    if(Motor1.distanceToGo() == 0 && Motor2.distanceToGo() == 0 && Motor3.distanceToGo() == 0){
      Motor1.setCurrentPosition(-208); //homing ke -15 derajat
      Motor2.setCurrentPosition(-208);
      Motor3.setCurrentPosition(-208);    
      homing_complete = 2;
      break;
    }
  }


  while(homing_complete == 2){
    if (digitalRead(limitW)) {
       MotorW.moveTo(9999);
       MotorW.run(); 
   }
   else {
       doneW = 1;
   }
   if (doneW == 1){
      homing_complete = 3;
      MotorW.setCurrentPosition(0); 
      break;
   }
  }

   while(homing_complete == 3){
    MotorW.moveTo(-5);
    MotorW.run();

    if(MotorW.distanceToGo() == 0){
      MotorW.setCurrentPosition(0);
      digitalWrite(gripper, 0);
      delay(200);
      digitalWrite(gripper, 1);
      homing_complete = 4;
      Serial.println("h_done");
      x = 0;
      y = 0;
      z = 0;
      w = 0;      
      break;
    }
   }
}

int invers_kinematik(float ikx, float iky, float ikz, float ikw){

ikz = ikz - 220;

double a = (sqrt(3)/2)*(rp-rb);
double b = (0.5)*(rp-rb);
double c = rp - rb;
double E[3] = { lb*((sqrt(3)*(ikx-a))+iky-b), (-1)*2*lb*(iky+c), (-1)*lb*((sqrt(3)*(ikx+a))+b-iky)};
double F[3] = { 2*ikz*lb, 2*ikz*lb, 2*ikz*lb };
double G[3] = { pow(ikx,2) + pow(iky,2) + pow(ikz,2) + pow(lb,2) + pow(a,2) + pow(b,2) - (2*a*ikx) - (2*b*iky) - pow(lp,2), 
                pow(ikx,2) + pow(iky,2) + pow(ikz,2) + pow(lb,2) + pow(c,2) + (2*iky*c) - pow(lp,2), 
                pow(ikx,2) + pow(iky,2) + pow(ikz,2) + pow(lb,2) + pow(a,2) + pow(b,2) + (2*a*ikx) - (2*b*iky) - pow(lp,2)};



for (int i=0; i<3; i++){
    r[i] = sqrt((pow(E[i],2))+(pow(F[i],2)));
    psi[i] = acos(E[i]/r[i]);
    Giri[i] = G[i]/r[i];
    double hasilrad = (acos(Giri[i])+psi[i])-PI;
    double hasildeg = hasilrad*180/PI;
    theta[i] = (-1)*(hasildeg);
   
    if (theta[i] >= limitatas && theta[i] <= limitbawah){
        hasilth[i] = theta[i];
    }
    else{ 
        hasilth[i] = sqrt(-1);
    }
}

if (isnan(hasilth[0]) == 0 && isnan(hasilth[1]) == 0  && isnan(hasilth[2]) == 0) {
    theta1 = hasilth[0];
    theta2 = hasilth[1];
    theta3 = hasilth[2];
    //thetaW = 0;
    f1 = 0;
}
else {
    theta1 = 0;
    theta2 = 0;
    theta3 = 0;
    //thetaW = 0; 
    f1 = -1;
}      

return f1;
}


String getValue(String data, char separator, int index)
{
    int found = 0;
    int strIndex[] = { 0, -1 };
    int maxIndex = data.length() - 1;

    for (int i = 0; i <= maxIndex && found <= index; i++) {
        if (data.charAt(i) == separator || i == maxIndex) {
            found++;
            strIndex[0] = strIndex[1] + 1;
            strIndex[1] = (i == maxIndex) ? i+1 : i;
        }
    }
    return found > index ? data.substring(strIndex[0], strIndex[1]) : "";
}

void deg2pulse(float t1, float t2, float t3, float w){
  pt1 = int(t1*step123/degree123W);
  pt2 = int(t2*step123/degree123W);
  pt3 = int(t3*step123/degree123W);
  ptw = int(w*stepW/degree123W);
}


int moveRobot(int p1,int p2,int p3,int pw)
{  
  Motor1.moveTo(p1);
  Motor2.moveTo(p2);
  Motor3.moveTo(p3);
  MotorW.moveTo(pw);
  Motor1.run();
  Motor2.run();
  Motor3.run();
  MotorW.run();

  if(Motor1.distanceToGo() == 0 && Motor2.distanceToGo() == 0 && Motor3.distanceToGo() == 0 && MotorW.distanceToGo() == 0){
    return 1;
  }
  else{
    return 0;
  }
}

void titik(float sx, float sy, float sz, float sw){
  x = sx;
  y = sy;
  z = sz;
  w = sw;
}

void siklus_robot(float jx, float jy,float jz, float jw)
{
  bool runsiklus = true;
  siklus=1;
  while(runsiklus){
     
  if (siklus == 1){ //keposisi benda
    titik(jx, jy, jz, jw);  
    int exist = invers_kinematik(x, y, z, w);
    if (exist == 0){
    deg2pulse(theta1, theta2, theta3, thetaW);
    int stat = moveRobot(pt1, pt2, pt3, ptw);
    if (stat==1)siklus++;
    }
    //Serial.println(exist);
  }
  
  else if (siklus == 2){ //z turun
    titik(jx, jy, -200, jw);
    int exist = invers_kinematik(x, y, z, w);
    if (exist==0){
    deg2pulse(theta1, theta2, theta3, thetaW);
    int stat = moveRobot(pt1, pt2, pt3, ptw);
    if (stat==1)siklus++;
  }
  }
  else if (siklus == 3){ //grip benda
    digitalWrite(gripper,0);
    delay(10);
    siklus++;
  }

  else if (siklus == 4){ //z naik
    titik(jx, jy, jz, jw);
    int exist = invers_kinematik(x, y, z, w);
    if (exist==0){
    deg2pulse(theta1, theta2, theta3, thetaW);
    int stat = moveRobot(pt1, pt2, pt3, ptw);
    if (stat==1)siklus++;
  }
  }

  else if (siklus == 5){ //keposisi place
    titik(175, 55, jz, 0);
    int exist = invers_kinematik(x, y, z, w);
    if (exist==0){
    deg2pulse(theta1, theta2, theta3, thetaW);
    int stat = moveRobot(pt1, pt2, pt3, ptw);
    if (stat==1)siklus++;
  }
  }

  else if (siklus == 6){ //z turun
    titik(175, 55, -200, 0);
    int exist = invers_kinematik(x, y, z, w);
    if (exist==0){
    deg2pulse(theta1, theta2, theta3, thetaW);
    int stat = moveRobot(pt1, pt2, pt3, ptw);
    if (stat==1)siklus++;
  }
  }
  else if (siklus == 7){ //lepas benda
    digitalWrite(gripper,1);
    delay(10);
    siklus++;
  }

  else if (siklus == 8){ //z naik
    titik(195, 55, jz, 0);
    int exist = invers_kinematik(x, y, z, w);
    if (exist==0){
    deg2pulse(theta1, theta2, theta3, thetaW);
    int stat = moveRobot(pt1, pt2, pt3, ptw);
    if (stat==1)siklus++;
  }
  }
  else if (siklus == 9){ //homing
    homing();
    if (homing_complete == 4) siklus++;
  }

  else if (siklus == 10){
    Serial.println("pnp_done");
    runsiklus = false;
    break;
  }

  Serial.println(siklus);
  }
}

void robot_manual_move(float mx, float my,float mz, float mw){
  bool man = true;
  
  while(man){
  x = x + mx;
  y = y + my;
  z = z + mz;
  w = w + mw;

  int exist = invers_kinematik(x, y, z, w);
    if (exist==0){
  deg2pulse(theta1, theta2, theta3, thetaW);
  int stat = moveRobot(pt1, pt2, pt3, ptw);
  if (stat==1){
    man = false;
    break; 
  }
  }
  }
}

void loop() {

  homing();
  siklus_robot(50,50,-100,0);
  
  if (Serial.available()>0){
    String data = Serial.readStringUntil('\n');
    
    int address = getValue(data, ',', 0).toInt();

    if(address == 1){
      String sx = getValue(data, ',', 1);
      String sy = getValue(data, ',', 2);
      String sz = getValue(data, ',', 3);
      String sw = getValue(data, ',', 4);
      siklus = 1;
      siklus_robot(sx.toFloat(), sy.toFloat() + offsetcam, sz.toFloat(), sw.toFloat());   
      }
      
    else if(address == 2){
      String man_x = getValue(data, ',', 1);
      String man_y = getValue(data, ',', 2);
      String man_z = getValue(data, ',', 3);
      String man_w = getValue(data, ',', 4);
      robot_manual_move(man_x.toFloat(), man_y.toFloat(), man_z.toFloat(), man_w.toFloat());
      }
      
    else if(address == 3) homing();
    
    else if(address == 4){
      int grip_en = getValue(data, ',', 1).toInt();
      digitalWrite(gripper,grip_en);
      }
    
    if (!data) Serial.end();
  }
} 
