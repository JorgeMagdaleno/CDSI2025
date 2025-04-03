import 'dart:convert';
import 'dart:math';

import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../Models/concept_model.dart';
import '../Models/gesture_model.dart';

class GameScreen1 extends StatefulWidget {
  @override
  _GameScreen1State createState() => _GameScreen1State();
}

class _GameScreen1State extends State<GameScreen1> with TickerProviderStateMixin {
  late AnimationController _controller;
  final int dropDuration = 5;
  int score = 0;
  Concept_model? currentConcept;
  bool isDragging = false;
  bool conceptsLoaded = false;
  bool gameOver = false;

  int totalCategorized = 0;
  final int maxConcepts = 10;

  bool tutorialShown = false;
  bool tutorialActive = false;
  GlobalKey fallingConceptKey = GlobalKey();
  GlobalKey leftDropKey = GlobalKey();
  GlobalKey rightDropKey = GlobalKey();

  late Gesture_model leftGesture;
  late Gesture_model rightGesture;

  List<Concept_model> concepts = [];

  @override
  void initState() {
    super.initState();
    leftGesture = Gesture_model("Assets/nivel_1/A6.png");
    rightGesture = Gesture_model("Assets/nivel_1/B.png");

    _controller = AnimationController(
      vsync: this,
      duration: Duration(seconds: dropDuration),
    );
    _controller.addStatusListener((status) {
      if (status == AnimationStatus.completed && !isDragging && !gameOver) {
        setState(() {
          score--;
          totalCategorized++;
        });
        if (totalCategorized >= maxConcepts) {
          gameOver = true;
          _controller.stop();
          Future.delayed(Duration(milliseconds: 300), () {
            showGameOverDialog();
          });
        } else {
          spawnNewConcept();
        }
      }
    });

    loadConcepts();
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
      concepts = loadedConcepts;
      conceptsLoaded = true;
    });
    spawnNewConcept();
  }

  void spawnNewConcept() {
    if (concepts.isEmpty || gameOver) return;
    setState(() {
      isDragging = false;
      _controller.reset();
      currentConcept = concepts[Random().nextInt(concepts.length)];
      _controller.forward();
    });
    if (!tutorialShown && !tutorialActive) {
      Future.delayed(Duration(seconds: 1), () {
        if (!tutorialShown && mounted && currentConcept != null) {
          runTutorial();
        }
      });
    }
  }

  void runTutorial() {
    _controller.stop();
    setState(() {
      tutorialActive = true;
    });
    WidgetsBinding.instance.addPostFrameCallback((_) {
      RenderBox conceptBox = fallingConceptKey.currentContext!.findRenderObject() as RenderBox;
      Offset conceptPos = conceptBox.localToGlobal(Offset.zero);
      Size conceptSize = conceptBox.size;

      String targetGestureName = currentConcept!.gesture;
      GlobalKey targetKey = (targetGestureName.contains(leftGesture.name!))
          ? leftDropKey
          : rightDropKey;
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
                child: Image.asset(
                  currentConcept!.image,
                  width: conceptSize.width,
                  height: conceptSize.height,
                  fit: BoxFit.contain,
                ),
              );
            },
          );
        },
      );

      Overlay.of(context)!.insert(overlayEntry);
      animController.forward().then((value) {
        overlayEntry.remove();
        handleDrop(targetGestureName);
        setState(() {
          tutorialActive = false;
          tutorialShown = true;
        });
      });
    });
  }

  void handleDrop(String targetGestureName) {
    if (currentConcept != null && !gameOver) {
      setState(() {
        if (currentConcept!.gesture == targetGestureName ||
            currentConcept!.gesture.contains(targetGestureName)) {
          score++;
        } else {
          score--;
        }
        totalCategorized++;
      });
      if (totalCategorized >= maxConcepts) {
        gameOver = true;
        _controller.stop();
        Future.delayed(Duration(milliseconds: 300), () {
          showGameOverDialog();
        });
      } else {
        spawnNewConcept();
      }
    }
  }

  void showGameOverDialog() {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => AlertDialog(
        title: Text("Juego Terminado"),
        content: Text("Conceptos categorizados: $totalCategorized\nPuntuación final: $score"),
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
      totalCategorized = 0;
      gameOver = false;
    });
    spawnNewConcept();
  }

  Widget buildFallingConcept(Color borderColor) {
    return Container(
      key: fallingConceptKey,
      width: 60,
      height: 60,
      padding: EdgeInsets.all(5),
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        border: Border.all(color: borderColor, width: 4),
      ),
      child: ClipOval(
        child: Image.asset(
          currentConcept!.image,
          width: 50,
          height: 50,
          fit: BoxFit.contain,
        ),
      ),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text("Juego LSM Prototipo - Juego 1")),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(8.0),
            child: Text("Puntuación: $score", style: TextStyle(fontSize: 24)),
          ),
          Expanded(
            child: conceptsLoaded
                ? Row(
              children: [
                Expanded(
                  child: DragTarget<Concept_model>(
                    key: leftDropKey,
                    onAccept: (data) {
                      handleDrop(leftGesture.name!);
                    },
                    builder: (context, candidateData, rejectedData) {
                      return Container(
                        margin: EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          border: Border.all(color: Colors.blue, width: 2),
                        ),
                        child: Center(
                          child: Image.asset(
                            leftGesture.image,
                            width: 60,
                            height: 60,
                            fit: BoxFit.contain,
                          ),
                        ),
                      );
                    },
                  ),
                ),
                Expanded(
                  child: LayoutBuilder(
                    builder: (context, constraints) {
                      return Stack(
                        children: [
                          AnimatedBuilder(
                            animation: _controller,
                            builder: (context, child) {
                              double top = _controller.value * (constraints.maxHeight - 60);
                              final borderColor = Color.lerp(Colors.green, Colors.red, _controller.value)!;
                              return Positioned(
                                top: top,
                                left: (constraints.maxWidth - 60) / 2,
                                child: currentConcept != null
                                    ? Draggable<Concept_model>(
                                  data: currentConcept,
                                  child: buildFallingConcept(borderColor),
                                  feedback: buildFallingConcept(borderColor),
                                  childWhenDragging: Container(),
                                  onDragStarted: () {
                                    setState(() {
                                      isDragging = true;
                                      _controller.stop();
                                    });
                                  },
                                  onDraggableCanceled: (velocity, offset) {
                                    setState(() {
                                      score--;
                                      totalCategorized++;
                                    });
                                    if (totalCategorized >= maxConcepts) {
                                      gameOver = true;
                                      _controller.stop();
                                      Future.delayed(Duration(milliseconds: 300), () {
                                        showGameOverDialog();
                                      });
                                    } else {
                                      spawnNewConcept();
                                    }
                                  },
                                )
                                    : Container(),
                              );
                            },
                          ),
                        ],
                      );
                    },
                  ),
                ),
                Expanded(
                  child: DragTarget<Concept_model>(
                    key: rightDropKey,
                    onAccept: (data) {
                      handleDrop(rightGesture.name!);
                    },
                    builder: (context, candidateData, rejectedData) {
                      return Container(
                        margin: EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          border: Border.all(color: Colors.red, width: 2),
                        ),
                        child: Center(
                          child: Image.asset(
                            rightGesture.image,
                            width: 60,
                            height: 60,
                            fit: BoxFit.contain,
                          ),
                        ),
                      );
                    },
                  ),
                ),
              ],
            )
                : Center(child: CircularProgressIndicator()),
          ),
        ],
      ),
    );
  }
}