import 'package:polymer/builder.dart';

void main() {
  build(entryPoints: ['web/pastee.html'],
        options: parseOptions(['--deploy']));
}
