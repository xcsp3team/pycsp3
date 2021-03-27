// import org.chocosolver.parser.xcsp.XCSP;
// import org.chocosolver.parser.xcsp.BaseXCSPListener;
// import org.chocosolver.pf4cs.SetUpException;
// import py4j.GatewayServer;
//
// public class ChocoSolverPy4J {
//
//     public void loadXCSP3(String xml) {
//         System.out.println(xml);
//         XCSP xscp = new XCSP();
//         xscp.addListener(new BaseXCSPListener(xscp));
//         String[] args = new String[]{xml};
//         try{
//             xscp.setUp(args);
//         }catch (SetUpException sx){
//             throw new RuntimeException(sx.getCause());
//         }
//         xscp.createSolver();
//         xscp.buildModel();
//         xscp.configureSearch();
//         xscp.solve();
//     }
//
//     public ChocoSolverPy4J() {}
//
//     public ChocoSolverPy4J getSolver() {
//         return this;
//     }
//
//     public static void main(String[] argv) {
//         GatewayServer gatewayServer = new GatewayServer(new ChocoSolverPy4J());
//         gatewayServer.start();
//         System.out.println("ChocoSolverPy4J Gateway Server Started");
//     }
// }