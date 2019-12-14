import abscon.Resolution;
import dashboard.Arguments;
import py4j.GatewayServer;

public class AbsConPy4J {

    public void loadXCSP3(String xml) {
        System.out.println(xml);
        Arguments.loadArguments(xml);
    }

    public AbsConPy4J() {}

    public AbsConPy4J getSolver() {
        return this;
    }

    public static void main(String[] argv) {
        GatewayServer gatewayServer = new GatewayServer(new AbsConPy4J());
        gatewayServer.start();
        System.out.println("AbsConPy4J Gateway Server Started");
    }
}