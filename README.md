# IABKivy
*In-app billing in Kivy Applications*

This repository contains a working demo application build with Kivy which allows you to embed in-app purchasing using
google play.

<img src="demo.gif" width="324" height="576">

### Note
* If you want to test this app on your device, you need to install it using adb as:
  ```
  adb install -i com.android.vending path/to/your/apk
  ```
* Don't worry if you see an error saying the item is not available. It's because it needs your app to be published on the playstore in order to get correct products.
