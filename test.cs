using System;
using System.IO;

class Program {
    static void Main() {
        string path = @"c:\Users\李超超\Desktop\知识";
        Console.WriteLine(Path.GetFullPath(path));
    }
}