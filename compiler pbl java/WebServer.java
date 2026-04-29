import com.sun.net.httpserver.*;
import java.io.*;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Map;

public class WebServer {
    private static final int PORT = 8080;
    private HttpServer server;

    public WebServer() throws IOException {
        server = HttpServer.create(new InetSocketAddress("localhost", PORT), 0);
        server.createContext("/api/compile", new CompileHandler());
        server.createContext("/", new RootHandler());
        server.setExecutor(null);
    }

    public void start() {
        server.start();
        System.out.println("Web server started on http://localhost:" + PORT);
    }

    public void stop() {
        server.stop(0);
    }

    // Handler for the root path (serves frontend)
    static class RootHandler implements HttpHandler {
        @Override
        public void handle(HttpExchange exchange) throws IOException {
            String path = exchange.getRequestURI().getPath();
            String response;

            if (path.equals("/") || path.equals("/frontend1.html")) {
                response = readFile("frontend1.html");
                exchange.getResponseHeaders().set("Content-Type", "text/html; charset=utf-8");
            } else if (path.equals("/front.html")) {
                response = readFile("front.html");
                exchange.getResponseHeaders().set("Content-Type", "text/html; charset=utf-8");
            } else {
                exchange.getResponseHeaders().set("Content-Type", "text/plain");
                response = "404 Not Found";
                exchange.sendResponseHeaders(404, response.getBytes().length);
                OutputStream os = exchange.getResponseBody();
                os.write(response.getBytes());
                os.close();
                return;
            }

            byte[] bytes = response.getBytes(StandardCharsets.UTF_8);
            exchange.sendResponseHeaders(200, bytes.length);
            OutputStream os = exchange.getResponseBody();
            os.write(bytes);
            os.close();
        }

        private String readFile(String filename) throws IOException {
            StringBuilder sb = new StringBuilder();
            try (BufferedReader br = new BufferedReader(new FileReader(filename))) {
                String line;
                while ((line = br.readLine()) != null) {
                    sb.append(line).append("\n");
                }
            }
            return sb.toString();
        }
    }

    // Handler for compilation API
    static class CompileHandler implements HttpHandler {
        @Override
        public void handle(HttpExchange exchange) throws IOException {
            // Enable CORS
            exchange.getResponseHeaders().set("Access-Control-Allow-Origin", "*");
            exchange.getResponseHeaders().set("Access-Control-Allow-Methods", "POST, GET, OPTIONS");
            exchange.getResponseHeaders().set("Access-Control-Allow-Headers", "Content-Type");

            if (exchange.getRequestMethod().equalsIgnoreCase("OPTIONS")) {
                exchange.sendResponseHeaders(200, -1);
                return;
            }

            if (!exchange.getRequestMethod().equalsIgnoreCase("POST")) {
                String response = "{\"error\": \"Only POST requests are allowed\"}";
                exchange.getResponseHeaders().set("Content-Type", "application/json");
                exchange.sendResponseHeaders(400, response.getBytes().length);
                exchange.getResponseBody().write(response.getBytes());
                exchange.getResponseBody().close();
                return;
            }

            try {
                // Read request body
                InputStream is = exchange.getRequestBody();
                BufferedReader reader = new BufferedReader(new InputStreamReader(is, StandardCharsets.UTF_8));
                StringBuilder requestBody = new StringBuilder();
                String line;
                while ((line = reader.readLine()) != null) {
                    requestBody.append(line);
                }

                // Parse JSON to get the code
                String jsonRequest = requestBody.toString();
                String code = extractCodeFromJson(jsonRequest);

                // Redirect stdout to capture output
                PrintStream originalOut = System.out;
                ByteArrayOutputStream baos = new ByteArrayOutputStream();
                System.setOut(new PrintStream(baos));

                try {
                    // Compile the code
                    String result = compileCode(code);

                    // Restore stdout
                    System.setOut(originalOut);
                    String capturedOutput = baos.toString(StandardCharsets.UTF_8);

                    // Send response
                    String response = "{\"success\": true, \"result\": " + result + ", \"output\": \"" 
                        + escapeJson(capturedOutput) + "\"}";
                    
                    exchange.getResponseHeaders().set("Content-Type", "application/json");
                    byte[] bytes = response.getBytes(StandardCharsets.UTF_8);
                    exchange.sendResponseHeaders(200, bytes.length);
                    exchange.getResponseBody().write(bytes);
                    exchange.getResponseBody().close();

                } catch (Exception e) {
                    System.setOut(originalOut);
                    String errorMessage = e.getMessage() != null ? e.getMessage() : e.toString();
                    String capturedOutput = baos.toString(StandardCharsets.UTF_8);
                    String response = "{\"success\": false, \"error\": \"" + escapeJson(errorMessage) 
                        + "\", \"output\": \"" + escapeJson(capturedOutput) + "\"}";
                    
                    exchange.getResponseHeaders().set("Content-Type", "application/json");
                    byte[] bytes = response.getBytes(StandardCharsets.UTF_8);
                    exchange.sendResponseHeaders(200, bytes.length);
                    exchange.getResponseBody().write(bytes);
                    exchange.getResponseBody().close();
                }

            } catch (Exception e) {
                String response = "{\"error\": \"" + escapeJson(e.toString()) + "\"}";
                exchange.getResponseHeaders().set("Content-Type", "application/json");
                exchange.sendResponseHeaders(500, response.getBytes().length);
                exchange.getResponseBody().write(response.getBytes());
                exchange.getResponseBody().close();
            }
        }

        private String compileCode(String code) throws Exception {
            StringBuilder result = new StringBuilder();
            result.append("{");

            // Step 1: Tokenization
            result.append("\"tokens\": ");
            try {
                Lexer lexer = new Lexer(code);
                List<Token> tokens = lexer.tokenize();
                result.append(tokensToJson(tokens)).append(", ");
                System.out.println("=== TOKENS ===");
                tokens.forEach(t -> System.out.println(t));

                // Step 2: Syntax Analysis
                result.append("\"syntax\": ");
                try {
                    Syntax parser = new Syntax(tokens);
                    Syntax.ParseNode root = parser.parse();
                    result.append(parseNodeToJson(root)).append(", ");
                    System.out.println("\n=== PARSE TREE ===");
                    root.print("", true);

                    // Step 3: Semantic Analysis
                    result.append("\"semantic\": ");
                    try {
                        Semantic semantic = new Semantic(tokens);
                        semantic.analyze();
                        Map<String, Semantic.SymbolInfo> symbolTable = semantic.getSymbolTable();
                        result.append(symbolTableToJson(symbolTable)).append(", ");
                        System.out.println("\n=== SYMBOL TABLE ===");
                        symbolTable.forEach((k, v) -> System.out.println(k + " -> " + v.type + " = " + v.value));

                        // Step 4: IR Generation
                        result.append("\"ir\": ");
                        try {
                            IRGenerator irGen = new IRGenerator(tokens, symbolTable);
                            List<String> ir = irGen.generate();
                            result.append(irToJson(ir));
                            System.out.println("\n=== INTERMEDIATE CODE ===");
                            ir.forEach(System.out::println);
                        } catch (Exception e) {
                            result.append("{\"error\": \"").append(escapeJson(e.toString())).append("\"}");
                            System.out.println("IR Generation Error: " + e.getMessage());
                        }

                    } catch (Exception e) {
                        result.append("{\"error\": \"").append(escapeJson(e.toString())).append("\"}");
                        System.out.println("Semantic Analysis Error: " + e.getMessage());
                    }

                } catch (Exception e) {
                    result.append("{\"error\": \"").append(escapeJson(e.toString())).append("\"}");
                    System.out.println("Syntax Analysis Error: " + e.getMessage());
                }

            } catch (Exception e) {
                result.append("{\"error\": \"").append(escapeJson(e.toString())).append("\"}");
                System.out.println("Tokenization Error: " + e.getMessage());
            }

            result.append("}");
            return result.toString();
        }

        private String tokensToJson(List<Token> tokens) {
            StringBuilder sb = new StringBuilder("[");
            for (int i = 0; i < tokens.size(); i++) {
                Token t = tokens.get(i);
                sb.append("{\"type\": \"").append(t.type).append("\", \"value\": \"").append(escapeJson(t.value)).append("\"}");
                if (i < tokens.size() - 1) sb.append(", ");
            }
            sb.append("]");
            return sb.toString();
        }

        private String parseNodeToJson(Syntax.ParseNode node) {
            StringBuilder sb = new StringBuilder("{");
            sb.append("\"label\": \"").append(escapeJson(node.label)).append("\"");
            if (!node.children.isEmpty()) {
                sb.append(", \"children\": [");
                for (int i = 0; i < node.children.size(); i++) {
                    sb.append(parseNodeToJson(node.children.get(i)));
                    if (i < node.children.size() - 1) sb.append(", ");
                }
                sb.append("]");
            }
            sb.append("}");
            return sb.toString();
        }

        private String symbolTableToJson(Map<String, Semantic.SymbolInfo> table) {
            StringBuilder sb = new StringBuilder("{");
            int i = 0;
            for (Map.Entry<String, Semantic.SymbolInfo> entry : table.entrySet()) {
                Semantic.SymbolInfo info = entry.getValue();
                sb.append("\"").append(entry.getKey()).append("\": {");
                sb.append("\"type\": \"").append(info.type).append("\", ");
                sb.append("\"value\": \"").append(info.value).append("\", ");
                sb.append("\"initialized\": ").append(info.isInitialized);
                sb.append("}");
                if (i < table.size() - 1) sb.append(", ");
                i++;
            }
            sb.append("}");
            return sb.toString();
        }

        private String irToJson(List<String> ir) {
            StringBuilder sb = new StringBuilder("[");
            for (int i = 0; i < ir.size(); i++) {
                sb.append("\"").append(escapeJson(ir.get(i))).append("\"");
                if (i < ir.size() - 1) sb.append(", ");
            }
            sb.append("]");
            return sb.toString();
        }

        private String extractCodeFromJson(String json) {
            // Simple JSON parsing for "code" field
            int start = json.indexOf("\"code\":");
            if (start == -1) return "";
            start = json.indexOf("\"", start + 7);
            if (start == -1) return "";
            int end = json.indexOf("\"", start + 1);
            if (end == -1) return "";
            String code = json.substring(start + 1, end);
            // Unescape JSON string
            code = code.replace("\\n", "\n").replace("\\t", "\t").replace("\\\"", "\"").replace("\\\\", "\\");
            return code;
        }

        private String escapeJson(String text) {
            if (text == null) return "";
            return text.replace("\\", "\\\\")
                      .replace("\"", "\\\"")
                      .replace("\n", "\\n")
                      .replace("\r", "\\r")
                      .replace("\t", "\\t");
        }
    }

    public static void main(String[] args) {
        try {
            WebServer ws = new WebServer();
            ws.start();
            System.in.read(); // Keep running until user inputs
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
