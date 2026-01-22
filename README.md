# Why

After a long time actively avoiding learning Rust, I’ve decided to push myself and finally give it a try, driven by all the hype and FOMO specially for blockchain projects.

The book Building Bitcoin in Rust by Lukáš Hozda has been a gem, delving deeply into both the practicalities of blockchain design and aproaching to Rust.
However, what I decided to do here, was to write side-by-side versions of the Rust code alongside a Python equivalent, with a double purpose:

A), because it serves me a Rosetta stone to understand that thing A, is the same thing as thing B in Python. With the succint algebraic syntax of Rust, it makes easier to just know -oh, this is just this...

A) because it serves me as a Rosetta stone to understand that "thing A" is the same as "thing B" in Python. With Rust's sometimes algebraic syntax, it becomes easier to recognize: "okay, this is just ..."

B) because I’m finding hard to buy the two main arguments for the Rust hype: security and speed.

About security, there is a plethora of safety nets in almost every programming language to avoid side effects. Just write immutable!
The argument usually goes like: "yeah, but you have to be disciplined about it… with Rust, the compiler forces you to."
So you're telling me that instead of knowing how to do your job, and doing it with an enabling and friendly language, the solution is to put fresh devs through an overly annoying language, and a compiler with which you need to spend hours to days fighting just to compile one line?

As for performance, I'm not convinced either. Sure Python is dang slow ..but I'm not seeing differences I would actually care about between doing the same thing in Rust vs. doing it in ie: TypeScript.
And I'd be willing to extend that argument to Python, in the light of its latest initiatives around compiling to C and the recent developments around JIT compilers.
