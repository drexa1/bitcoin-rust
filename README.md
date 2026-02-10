# Why

After a long time actively avoiding learning Rust 🦀, I’ve decided to push myself and finally give it a committed try, driven by all the hype and FOMO, especially for blockchain projects.

The book "Building Bitcoin in Rust"—by Lukáš Hozda has been a gem, delving deeply into both the practicalities of blockchain design and aproaching to Rust.  
However, what I decided to do here was to write side-by-side versions of the Rust code alongside a Python equivalent, with a double purpose:

+ a) because it serves me as a Rosetta stone to understand that "thing A" in Rust is just the same as "thing B" in Python. With Rust's sometimes abbreviated and algebraic syntax, it becomes easier to recognize: "okay, this is just [...]"

+ b) because I'm wrestling with the two main arguments for the Rust hype: **security** and **speed**.

About security, there is an assortment of mechanisms in almost every programming language to avoid side effects (Just write immutable code!).  
The argument I read goes like: "yeah, but you have to be disciplined about it... and with Rust, the compiler forces you."  
I'm dubious that instead of knowing how to do your job and doing it with an enabling and friendly language, the solution is to put devs through a language and a compiler where you need to spend hours/days fighting to compile one line.  

For performance, it's hard to say from my standpoint because the things I normally care about do not demand peak CPU performance. 
But I'd be willing to contest it, particularly in the light of the latest initiatives around compiling-optimizing Python to C and its recent developments in JIT libraries...

[EDIT]: After a couple of months, I have to admit that there is one argument which stands up untouched: the argument for mathematical correctness in math-sensitive operations.
