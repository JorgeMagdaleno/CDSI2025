import 'dart:async';
import 'dart:convert';
import 'dart:math';

import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:flutter/scheduler.dart';
import 'package:flutter/services.dart';

import '../Models/concept_model.dart';
import '../Models/gesture_model.dart';

class GameScreen2 extends StatefulWidget {
  @override
  _GameScreen2State createState() => _GameScreen2State();
}

class _GameScreen2State extends State<GameScreen2> with TickerProviderStateMixin {
  List<Concept_model> catalogueConcepts = [];
  List<Gesture_model> gestures = [];
  int score = 0;
  int correctCount = 0;
  bool gameOver = false;

  final double carouselRPM = 10;
  final int timeLimitSeconds = 60;
  Timer? _gameTimer;


  bool tutorialShown = false;
  bool tutorialActive = false;
  Concept_model? tutorialConcept;
  GlobalKey tutorialConceptKey = GlobalKey();

  Map<String, GlobalKey> carouselKeys = {};

  @override
  void initState() {
    super.initState();

    gestures = [
      Gesture_model("Assets/nivel_1/A6.png"),
      Gesture_model("Assets/nivel_1/B.png"),

    ];

    for (var gesture in gestures) {
      carouselKeys[gesture.name!] = GlobalKey();
    }
    loadConcepts();
    startTimer();
  }
  void startTimer() {
    _gameTimer?.cancel();
    _gameTimer = Timer(Duration(seconds: timeLimitSeconds), () {
      if (!gameOver) {
        setState(() {
          gameOver = true;
        });
        Future.delayed(Duration(milliseconds: 300), () {
          showGameOverDialog();
        });
      }
    });
  }


  Future<void> loadConcepts() async {
    final manifestContent = await rootBundle.loadString('AssetManifest.json');
    final Map<String, dynamic> manifestMap = json.decode(manifestContent);
    List<Concept_model> loadedConcepts = [];


    manifestMap.keys.forEach((String key) {
      if (key.startsWith('Assets/nivel_1/A6_ilustraciones/')) {
        loadedConcepts.add(Concept_model(key, "Assets/nivel_1/A6"));
      } else if (key.startsWith('Assets/nivel_1/B_ilustraciones/')) {
        loadedConcepts.add(Concept_model(key, "Assets/nivel_1/B"));
      }
    });

    setState(() {
      catalogueConcepts = loadedConcepts;
    });

    if (!tutorialShown && catalogueConcepts.isNotEmpty) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        runTutorial();
      });
    }
  }


  void runTutorial() {

    tutorialConcept = catalogueConcepts.first;

    setState(() {
      tutorialActive = true;
    });

    WidgetsBinding.instance.addPostFrameCallback((_) {

      RenderBox conceptBox = tutorialConceptKey.currentContext!.findRenderObject() as RenderBox;
      Offset conceptPos = conceptBox.localToGlobal(Offset.zero);
      Size conceptSize = conceptBox.size;


      String targetGestureName = tutorialConcept!.gesture;
      GlobalKey targetKey = carouselKeys[targetGestureName]!;
      RenderBox targetBox = targetKey.currentContext!.findRenderObject() as RenderBox;
      Offset targetPos = targetBox.localToGlobal(Offset.zero);
      Size targetSize = targetBox.size;


      Offset start = conceptPos + Offset(conceptSize.width / 2, conceptSize.height / 2);
      Offset end = targetPos + Offset(targetSize.width / 2, targetSize.height / 2);


      AnimationController animController = AnimationController(vsync: this, duration: Duration(seconds: 2));
      Animation<Offset> positionAnimation = Tween<Offset>(begin: start, end: end)
          .animate(CurvedAnimation(parent: animController, curve: Curves.easeInOut));


      OverlayEntry overlayEntry = OverlayEntry(
        builder: (context) {
          return AnimatedBuilder(
            animation: animController,
            builder: (context, child) {
              return Positioned(
                left: positionAnimation.value.dx - conceptSize.width / 2,
                top: positionAnimation.value.dy - conceptSize.height / 2,
                child: Opacity(
                  opacity: 1.0,
                  child: Image.asset(
                    tutorialConcept!.image,
                    width: conceptSize.width,
                    height: conceptSize.height,
                    fit: BoxFit.contain,
                  ),
                ),
              );
            },
          );
        },
      );


      Overlay.of(context)!.insert(overlayEntry);

      animController.forward().then((value) {

        overlayEntry.remove();
        handleDrop(targetGestureName, tutorialConcept!);

        setState(() {
          tutorialActive = false;
          tutorialShown = true;
        });
      });
    });
  }


  void handleDrop(String targetGestureName, Concept_model concept) {
    if (gameOver) return;
    setState(() {
      if (concept.gesture == targetGestureName) {
        score++;
        correctCount++;
      } else {
        score--;
      }

      catalogueConcepts.remove(concept);
    });

    if (catalogueConcepts.isEmpty) {
      setState(() {
        gameOver = true;
      });
      _gameTimer?.cancel();
      Future.delayed(Duration(milliseconds: 300), () {
        showGameOverDialog();
      });
    }
  }


  void showGameOverDialog() {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => AlertDialog(
        title: Text("Juego Terminado"),
        content: Text("Respuestas correctas: $correctCount\nPuntuación final: $score"),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.of(context).pop();
              resetGame();
            },
            child: Text("Reiniciar"),
          ),
        ],
      ),
    );
  }


  void resetGame() {
    setState(() {
      score = 0;
      correctCount = 0;
      gameOver = false;
      tutorialShown = true;
    });
    loadConcepts();
    startTimer();
  }


  Widget buildCatalogueConcept(Concept_model concept) {

    return Container(
      key: (tutorialConcept != null && concept == tutorialConcept) ? tutorialConceptKey : null,
      decoration: BoxDecoration(
        border: Border.all(color: Colors.black54),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Image.asset(
        concept.image,
        fit: BoxFit.contain,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {

    return Scaffold(
      appBar: AppBar(title: Text("Juego LSM Prototipo - Juego 2")),
      body: Stack(
        children: [
          Column(
            children: [

              Container(
                height: 120,
                color: Colors.grey[200],
                child: CarouselRow(
                  gestures: gestures,
                  rpm: carouselRPM,
                  pause: tutorialActive,
                  onAccept: handleDrop,
                  gestureKeys: carouselKeys,
                ),
              ),
              Divider(),

              Expanded(
                child: Padding(
                  padding: const EdgeInsets.all(8.0),
                  child: LayoutBuilder(
                    builder: (context, constraints) {

                      const double desiredMinCellWidth = 120;
                      int crossAxisCount =
                      (constraints.maxWidth / desiredMinCellWidth).floor();
                      crossAxisCount = max(1, crossAxisCount);
                      return GridView.builder(
                        gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
                          crossAxisCount: crossAxisCount,
                          crossAxisSpacing: 8,
                          mainAxisSpacing: 8,
                        ),
                        itemCount: catalogueConcepts.length,
                        itemBuilder: (context, index) {
                          final concept = catalogueConcepts[index];
                          return Draggable<Concept_model>(
                            data: concept,
                            feedback: Material(
                              color: Colors.transparent,
                              child: SizedBox(
                                width: 120, // Set to your desired fixed width
                                height: 120, // Set to your desired fixed height
                                child: buildCatalogueConcept(concept),
                              ),
                            ),
                            childWhenDragging: SizedBox(
                              width: 120,
                              height: 120,
                              child: Container(color: Colors.grey[200]),
                            ),
                            child: SizedBox(
                              width: 120,
                              height: 120,
                              child: buildCatalogueConcept(concept),
                            ),
                          );
                        },
                      );
                    },
                  ),
                ),
              ),

              Padding(
                padding: const EdgeInsets.all(8.0),
                child: Text("Puntuación: $score", style: TextStyle(fontSize: 24)),
              ),
            ],
          ),

        ],
      ),
    );
  }
}



class CarouselRow extends StatefulWidget {
  final List<Gesture_model> gestures;
  final double rpm;
  final bool pause;
  final Function(String, Concept_model) onAccept;
  final Map<String, GlobalKey>? gestureKeys;

  CarouselRow({
    required this.gestures,
    required this.rpm,
    this.pause = false,
    required this.onAccept,
    this.gestureKeys,
  });

  @override
  _CarouselRowState createState() => _CarouselRowState();
}

class _CarouselRowState extends State<CarouselRow>
    with SingleTickerProviderStateMixin {
  late Ticker _ticker;
  double _elapsed = 0.0;

  @override
  void initState() {
    super.initState();
    _ticker = createTicker((elapsed) {
      if (!widget.pause) {
        setState(() {
          _elapsed = elapsed.inMilliseconds / 1000.0;
        });
      }
    });
    _ticker.start();
  }

  @override
  void dispose() {
    _ticker.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(builder: (context, constraints) {
      final double gap = 8.0;
      int count = widget.gestures.length;

      double itemWidth = (constraints.maxWidth - ((count + 1) * gap)) / count;
      double totalCycleWidth = count * (itemWidth + gap);

      double scrollSpeed = widget.rpm * totalCycleWidth / 60;
      double offset = (_elapsed * scrollSpeed) % totalCycleWidth;

      List<Widget> items = [];

      for (int i = 0; i < count; i++) {
        double baseX = i * (itemWidth + gap) + gap - offset;

        items.add(Positioned(
          left: baseX,
          top: 0,
          width: itemWidth,
          height: constraints.maxHeight,
          child: DragTarget<Concept_model>(

            key: widget.gestureKeys?[widget.gestures[i].name!],
            onAccept: (data) {
              widget.onAccept(widget.gestures[i].name!, data);
            },
            builder: (context, candidateData, rejectedData) {
              return Container(
                decoration: BoxDecoration(
                  border: Border.all(color: Colors.blue, width: 2),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Image.asset(
                  widget.gestures[i].image,
                  fit: BoxFit.contain,
                ),
              );
            },
          ),
        ));

        items.add(Positioned(
          left: baseX + totalCycleWidth,
          top: 0,
          width: itemWidth,
          height: constraints.maxHeight,
          child: DragTarget<Concept_model>(
            onAccept: (data) {
              widget.onAccept(widget.gestures[i].name!, data);
            },
            builder: (context, candidateData, rejectedData) {
              return Container(
                decoration: BoxDecoration(
                  border: Border.all(color: Colors.blue, width: 2),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Image.asset(
                  widget.gestures[i].image,
                  fit: BoxFit.contain,
                ),
              );
            },
          ),
        ));
      }
      return Stack(children: items);
    });
  }
}