from rdflib import Graph, Namespace
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
from SPARQLWrapper import SPARQLWrapper, JSON
import sys

# ---------------- TASK 1 ----------------
def task1():
    print("\n--- TASK 1: Largest neighbor for European countries (from local TTL) ---")

    g = Graph()
    try:
        g.parse("countrues_info.ttl", format="ttl")
    except Exception as e:
        print("Error loading TTL:", e)
        return

    EX = Namespace("http://example.com/demo/")

    query_countries = """
    PREFIX ex: <http://example.com/demo/>
    SELECT ?country WHERE {
        ?country a ex:Country ;
                 ex:part_of_continent <http://example.com/demo/Continent/EU> .
    }
    """

    try:
        europe_countries = [row[0] for row in g.query(query_countries)]
    except Exception as e:
        print("Error while querying countries:", e)
        return

    for country in europe_countries:
        query_neighbors = f"""
        PREFIX ex: <http://example.com/demo/>
        SELECT ?neighbor_country ?population WHERE {{
            <{country}> ex:has_country_neighbour ?nbres .
            ?nbres ex:country_neighbour_value ?neighbor_country .
            ?neighbor_country ex:population ?population .
        }}
        """

        try:
            neighbors = list(g.query(query_neighbors))
        except Exception as e:
            print(f"Query error for country {country}: {e}")
            continue

        if neighbors:
            try:
                best = max(neighbors, key=lambda x: int(x[1]))
                c_name = country.toPython().split("/")[-1]
                n_name = best[0].toPython().split("/")[-1]
                pop_val = str(best[1])
                print(f"{c_name} -> Largest-neighbor: {n_name} ({pop_val})")
            except Exception as e:
                print(f"Error processing neighbors for {country}: {e}")
        else:
            print(f"{country.toPython().split('/')[-1]} -> No neighbor data found")


# ---------------- TASK 2 ----------------
def task2():
    print("\n--- TASK 2: Oldest city in Ukraine (DBpedia) ---")

    import ssl
    ssl._create_default_https_context = ssl._create_unverified_context

    sparql = SPARQLWrapper("https://dbpedia.org/sparql")

    query = """
    PREFIX dbo: <http://dbpedia.org/ontology/>
    PREFIX dbp: <http://dbpedia.org/property/>
    PREFIX dbr: <http://dbpedia.org/resource/>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

    SELECT ?city ?year
    WHERE {
      ?city rdf:type dbo:City ;
            dbo:country dbr:Ukraine .

      {
        ?city dbo:foundingYear ?year .
      } UNION {
        ?city dbp:established ?year .
      } UNION {
        ?city dbp:foundation ?year .
      } UNION {
        ?city dbo:foundingDate ?date .
        BIND(year(?date) AS ?year)
      }

      FILTER( datatype(?year) = xsd:integer || datatype(?year) = xsd:gYear )
    }
    ORDER BY ASC(xsd:integer(?year))
    LIMIT 1
    """

    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)

    try:
        result = sparql.query().convert()
        row = result["results"]["bindings"][0]
        print("Oldest Ukrainian city (with known date):")
        print("City:", row["city"]["value"])
        print("Founded year:", row["year"]["value"])
    except Exception as e:
        print("Error querying DBpedia:", e)



# ---------------- TASK 3 ----------------
def task3():
    print("\n--- TASK 3: Ukrainian IT companies (DBpedia) ---")
    sparql = SPARQLWrapper("https://dbpedia.org/sparql")
    sparql.setReturnFormat(JSON)

    query = """
    PREFIX dbo: <http://dbpedia.org/ontology/>
    PREFIX dbr: <http://dbpedia.org/resource/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    SELECT DISTINCT ?company ?name ?foundingYear WHERE {
      ?company a dbo:Company ;
               rdfs:label ?name .

      FILTER (lang(?name) = "en")

      # компанія в Україні
      {
        ?company dbo:locationCountry dbr:Ukraine .
      } UNION {
        ?company dbo:country dbr:Ukraine .
      } UNION {
        ?company dbo:location dbr:Ukraine .
      } UNION {
        ?company dbo:headquarter dbr:Kyiv .
      }

      # індустрія або тип компанії
      OPTIONAL { ?company dbo:industry ?industry . }
      OPTIONAL { ?company dbo:product ?product . }
      OPTIONAL { ?company dbo:service ?service . }
      OPTIONAL { ?company dbo:genre ?genre . }

      FILTER (
        regex(str(?industry), "IT", "i") ||
        regex(str(?industry), "software", "i") ||
        regex(str(?industry), "computer", "i") ||
        regex(str(?industry), "technology", "i") ||
        regex(str(?industry), "electronics", "i") ||
        regex(str(?industry), "internet", "i") ||
        regex(str(?industry), "telecommunications", "i") ||
        regex(str(?product), "software", "i") ||
        regex(str(?service), "software", "i") ||
        regex(str(?genre), "technology", "i")
      )

      OPTIONAL { ?company dbo:foundingYear ?foundingYear }
    }
    ORDER BY ASC(?foundingYear)
    LIMIT 100
    """

    try:
        sparql.setQuery(query)
        result = sparql.query().convert()
        results = result["results"]["bindings"]

        if not results:
            print("No IT companies found.")
            return

        print(f"Found {len(results)} Ukrainian IT companies:\n")
        for row in results:
            name = row['name']['value']
            uri = row['company']['value']
            year = row['foundingYear']['value'] if 'foundingYear' in row else "Unknown"
            print(f"{name} — Founded: {year} — {uri}")

    except Exception as e:
        print("Error querying DBpedia:", e)
        
# ---------------- MAIN ----------------
def main():
    while True:
        print("\nSelect task to run:")
        print("1 - Task 1: Largest neighbor of European countries (local TTL)")
        print("2 - Task 2: Oldest city of Ukraine (DBpedia)")
        print("3 - Task 3: Ukrainian IT companies (DBpedia)")
        print("0 - Exit")
        choice = input("Enter your choice: ").strip()
        if choice == "1":
            task1()
        elif choice == "2":
            task2()
        elif choice == "3":
            task3()
        elif choice == "0":
            print("Exiting.")
            sys.exit(0)
        else:
            print("Invalid option, try again.")

if __name__ == "__main__":
    main()
