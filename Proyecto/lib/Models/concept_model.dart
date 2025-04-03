

class Concept_model {
  String? name;
  String image;
  String gesture;

  Concept_model(this.image,this.gesture){
    name = image.split(".")[0];
  }
}