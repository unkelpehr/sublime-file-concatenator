
+-----------------+
|                 |
| dependency-1.js |
|                 |
+-----------------+	// This should be at the absolute top // This should be stripped (but not the linebreak?) // This should be stripped (but not the linebreak?)
	+-----------------+
	|                 | // [Hello I am dependency 2!]
	| dependency-2.js |
	|                 |
	+-----------------+ // This should be intendated with one tab
+-----------------+
|                 | /* [Hello I am dependency 3!] */
| dependency-3.js |
|                 |
+-----------------+ // This should not have any intendation
			+-----------------+
			|                 | # [Hello I am dependency 4!]
			| dependency-4.js |
			|                 |
			+-----------------+ // This should be intendated with three tabs
import('test1-dependency-5.js') // This should be ignored (missing @)
													+-----------------+
													|                 |
													| dependency-6.js |
													|                 |
													+-----------------+ // This should be intendated 13 times
/*
 * This should not brake this comment section in any way. And it should be positioned immediately below this text.
 *
 * +-----------------+
 * |                 |
 * | dependency-7.js |
 * |                 |
 * +-----------------+
 * [This is the last line part of this comment section]
 */