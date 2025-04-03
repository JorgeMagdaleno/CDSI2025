import 'package:flutter/material.dart';
import 'package:juego_lsm/Game%20Screens/game_2.dart';

import 'Game Screens/game_1.dart';

void main() {
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Juego LSM Prototipo',
      theme: ThemeData(
        primarySwatch: Colors.blue,
      ),
      home: MenuPrincipal(),
      routes: {
        '/pagina1': (context) => GameScreen1(),
        '/pagina2': (context) => GameScreen2(),
      },
    );
  }
}

class MenuPrincipal extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: buildAppBar('Juego LSM Prototipo'),
      drawer: AppDrawer(),
      body: buildMainMenuBody(context),
    );
  }
}

AppBar buildAppBar(String title) {
  return AppBar(
    title: Text(title),
  );
}

Widget buildMainMenuBody(BuildContext context) {
  return Center(
    child: Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: <Widget>[
        ElevatedButton(
          child: Text('Juego 1'),
          onPressed: () {
            Navigator.pushNamed(context, '/pagina1');
          },
        ),
        SizedBox(height: 20),
        ElevatedButton(
          child: Text('Juego 2'),
          onPressed: () {
            Navigator.pushNamed(context, '/pagina2');
          },
        ),
      ],
    ),
  );
}

class AppDrawer extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Drawer(
      child: ListView(
        padding: EdgeInsets.zero,
        children: <Widget>[
          DrawerHeader(
            decoration: BoxDecoration(
              color: Colors.blue,
            ),
            child: Text(
              'Menú',
              style: TextStyle(
                color: Colors.white,
                fontSize: 24,
              ),
            ),
          ),
          ListTile(
            leading: Icon(Icons.bar_chart),
            title: Text('Estadísticas'),
            onTap: () {
              Navigator.pop(context);
            },
          ),
          ListTile(
            leading: Icon(Icons.settings),
            title: Text('Opciones'),
            onTap: () {
              Navigator.pop(context);
            },
          ),
          ListTile(
            leading: Icon(Icons.exit_to_app),
            title: Text('Cerrar sesión'),
            onTap: () {
              Navigator.pop(context);
            },
          ),
        ],
      ),
    );
  }
}
