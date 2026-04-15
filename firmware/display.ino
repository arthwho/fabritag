// --- ASCII LOADING ANIMATION ---
const char* loadingAnim[4][4] = {
  { "  ::::::", "   :   :", "  ::   :", "  ::  :::" },
  { "  ::  :::", "  ::   :", "   :   :", "  ::::::"  },
  { "  :::  ::", "   :   ::", "   :   :", "   ::::::" },
  { "   ::::::", "   :   :", "   :   ::", "  :::  ::" }
};
int currentAnimFrame = 0;

// --- SCREEN SAVER TIMER ---
unsigned long lastScreenUpdate = 0;
bool isScreenAsleep = false;

void updateScreen(String line1, String line2, String line3) {
  display.clearDisplay();
  display.setCursor(0, 0);
  display.println(line1);
  if (line2 != "") display.println(line2);
  if (line3 != "") display.println(line3);
  display.display();
  
  // Every time text is printed, wake up and reset the countdown!
  lastScreenUpdate = millis();
  isScreenAsleep = false;
}

// Check if it is time to sleep
//void handleScreenSaver() {
  // If the screen is awake AND 2000 milliseconds (2 seconds) have passed...
  //if (!isScreenAsleep && (millis() - lastScreenUpdate > 2000)) {
    //display.clearDisplay();
    //display.display(); // Push the black pixels to the hardware
    //isScreenAsleep = true;
  //}
//}

void drawLoadingAnim(String headerText) {
  display.clearDisplay();
  display.setCursor(0, 0);
  display.println(headerText);
  display.println(); // Empty line for spacing
  
  // Draw the 4 lines of the current animation frame
  for(int i = 0; i < 4; i++) {
    display.println(loadingAnim[currentAnimFrame][i]);
  }
  
  display.display();
  
  // Move to the next frame (loops back to 0 after 3)
  currentAnimFrame = (currentAnimFrame + 1) % 4;
}

// --- MULTITHREADING VARIABLES ---
volatile bool isAnimating = false;
volatile bool animationTaskRunning = false;
unsigned long animationStartTime = 0;
String currentLoadingText = "";

// The Background Task (Runs exclusively on Core 0)
void loadingAnimationTask(void * parameter) {
  animationTaskRunning = true;
  
  while (isAnimating) {
    drawLoadingAnim(currentLoadingText);
    vTaskDelay(250 / portTICK_PERIOD_MS); // Non-blocking delay for 250ms
  }
  
  animationTaskRunning = false;
  vTaskDelete(NULL); // Safely destroy the task when finished
}

// Controller Functions
void startLoading(String text) {
  currentLoadingText = text;
  isAnimating = true;
  animationStartTime = millis();

  // Launch the animation task on Core 0
  xTaskCreatePinnedToCore(
    loadingAnimationTask, "LoadingTask", 4096, NULL, 1, NULL, 0
  );
}

void stopLoading() {
  // 1. Enforce the minimum 4-frame (1000ms) rule
  while (millis() - animationStartTime < 1000) {
    delay(10); 
  }

  // 2. Tell the background task to stop spinning
  isAnimating = false;

  // 3. Wait for the task to safely finish drawing so the I2C bus doesn't crash
  while (animationTaskRunning) {
    delay(10);
  }
}