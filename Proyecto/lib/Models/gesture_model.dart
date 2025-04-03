
class Gesture_model {
  String? name;
  String image;
  Gesture_model(this.image){
    name = image.split(".")[0];
  }
}