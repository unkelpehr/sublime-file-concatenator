@import('test1-dependency-1.js')	// This should be at the absolute top
@import url('test1-dependency-non-existing.js') // This should be stripped (but not the linebreak?)
@import url('test1-dependency-non-existing-2.js') // This should be stripped (but not the linebreak?)
	// @import('test1-dependency-2.js') // This should be intendated with one tab
# 					@import('test1-dependency-3.js') // This should not have any intendation
			/* @import('test1-dependency-4.js')*/ // This should be intendated with three tabs
import('test1-dependency-5.js') // This should be ignored (missing @)
													@import('test1-dependency-6.js'); // This should be intendated 13 times
/*
 * This should not brake this comment section in any way. And it should be positioned immediately below this text.
 * @import('test1-dependency-7.js')
 * [This is the last line part of this comment section]
 */