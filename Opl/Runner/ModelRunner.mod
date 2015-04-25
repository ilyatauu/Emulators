main
{
   var source = new IloOplModelSource("..\\Models\\RPFGuan.mod");
   var def = new IloOplModelDefinition(source);
   var cplex = new IloCplex();
   var opl = new IloOplModel(def,cplex);
   
  var inputFilename = "..\\Problems\\RandomGeneration\\m8j5d15_0.csv";
  var inFile = new IloOplInputFile(inputFilename);
  
  var jobs = new Array();
  var readytimes = new Array();
  var processtimes = new Array();
  var duedates = new Array();
  var sizes = new Array();
  var boards_number;
  var line;
  line = inFile.readline();
  boards_number = parseInt(line);

  while (!inFile.eof)
  {
    line = inFile.readline();
    writeln(line);
    var data = line.split(",");
    var j =parseInt(data[0]); 
    jobs[j] = j; 
    processtimes[j] = parseInt(data[1]);
    duedates[j] = parseInt(data[2]);
    sizes[j] = parseInt(data[3]);
    readytimes[j] = parseInt(data[3]);
  }    
  inFile.close();
  
  var temp = new IloOplOutputFile("temp.dat");
  
  temp.writeln("jobs = {" + jobs.join(",") + "};");
  temp.writeln("M = " + boards_number + ";");
  temp.writeln("p = [" +  processtimes.join(",") + "];");
  temp.writeln("d = [" +  processtimes.join(",") + "];");
  temp.writeln("s = [" + sizes.join(",") + "];");
  temp.writeln("a = [" + readytimes.join(",") + "];" );
  
  temp.close();
  var data = new IloOplDataSource("temp.dat");
  opl.addDataSource(data);
  opl.generate();
  
  cplex.tilim = 300;
  cplex.solve();    
}