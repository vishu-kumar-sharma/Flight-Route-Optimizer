#include <iostream>
#include <vector>
#include <map>
#include <queue>
#include <set>
#include <algorithm>
#include <climits>
#include <string>
#include <sstream>
#include <fstream>
#include <cmath>
#include <cstdlib>

using namespace std;

struct Flight {
    string dest;
    int dist, time, fare;
    string flightNum;
};

struct Booking {
    int id;
    string passenger;
    string route;
    int fare;
    string seat;
};

class TrieNode {
public:
    map<char, TrieNode*> children;
    bool isEnd;
    TrieNode() : isEnd(false) {}
};

class Trie {
    TrieNode* root;

    void findSuggestions(TrieNode* node, string prefix, vector<string>& results) {
        if (node->isEnd) results.push_back(prefix);
        for (map<char, TrieNode*>::iterator it = node->children.begin();
             it != node->children.end(); ++it) {
            findSuggestions(it->second, prefix + it->first, results);
        }
    }

public:
    Trie() { root = new TrieNode(); }

    void insert(string word) {
        TrieNode* curr = root;
        for (size_t i = 0; i < word.length(); i++) {
            char c = word[i];
            if (curr->children.find(c) == curr->children.end()) {
                curr->children[c] = new TrieNode();
            }
            curr = curr->children[c];
        }
        curr->isEnd = true;
    }

    vector<string> autoComplete(string prefix) {
        TrieNode* curr = root;
        vector<string> results;
        for (size_t i = 0; i < prefix.length(); i++) {
            char c = prefix[i];
            if (curr->children.find(c) == curr->children.end()) return results;
            curr = curr->children[c];
        }
        findSuggestions(curr, prefix, results);
        return results;
    }
};

class BookingTree {
    struct Node {
        Booking data;
        Node *left, *right;
        Node(Booking b) : data(b), left(NULL), right(NULL) {}
    };

    Node* root;

    Node* insert(Node* node, Booking b) {
        if (!node) return new Node(b);
        if (b.id < node->data.id) node->left = insert(node->left, b);
        else node->right = insert(node->right, b);
        return node;
    }

    void inorder(Node* node, vector<Booking>& result) {
        if (!node) return;
        inorder(node->left, result);
        result.push_back(node->data);
        inorder(node->right, result);
    }

    Node* deleteNode(Node* node, int id) {
        if (!node) return NULL;
        if (id < node->data.id) {
            node->left = deleteNode(node->left, id);
        } else if (id > node->data.id) {
            node->right = deleteNode(node->right, id);
        } else {
            if (!node->left) {
                Node* temp = node->right;
                delete node;
                return temp;
            } else if (!node->right) {
                Node* temp = node->left;
                delete node;
                return temp;
            }
            Node* temp = node->right;
            while (temp->left) temp = temp->left;
            node->data = temp->data;
            node->right = deleteNode(node->right, temp->data.id);
        }
        return node;
    }

    Node* search(Node* node, int id) {
        if (!node || node->data.id == id) return node;
        if (id < node->data.id) return search(node->left, id);
        return search(node->right, id);
    }

public:
    BookingTree() : root(NULL) {}

    void addBooking(Booking b) {
        root = insert(root, b);
    }

    void cancelBooking(int id) {
        root = deleteNode(root, id);
    }

    Booking* findBooking(int id) {
        Node* node = search(root, id);
        return node ? &node->data : NULL;
    }

    vector<Booking> getAllBookings() {
        vector<Booking> result;
        inorder(root, result);
        return result;
    }
};

class FlightSystem {
    map<string, vector<Flight> > graph;
    Trie cityTrie;
    BookingTree bookings;
    int nextBookingId;

    string routeFile;
    string bookingFile;

    void mergeSort(vector<Flight>& arr, int l, int r, int mode) {
        if (l >= r) return;
        int m = l + (r - l) / 2;
        mergeSort(arr, l, m, mode);
        mergeSort(arr, m + 1, r, mode);

        vector<Flight> temp;
        int i = l, j = m + 1;
        while (i <= m && j <= r) {
            bool condition = false;
            if (mode == 1) condition = arr[i].fare < arr[j].fare;
            else if (mode == 2) condition = arr[i].time < arr[j].time;
            else condition = arr[i].dist < arr[j].dist;

            if (condition) temp.push_back(arr[i++]);
            else temp.push_back(arr[j++]);
        }
        while (i <= m) temp.push_back(arr[i++]);
        while (j <= r) temp.push_back(arr[j++]);

        for (size_t k = 0; k < temp.size(); k++) arr[l + k] = temp[k];
    }

    int heuristic(string a, string b) {
        int sum = 0;
        for (size_t i = 0; i < a.length(); i++) sum += a[i];
        for (size_t i = 0; i < b.length(); i++) sum -= b[i];
        return abs(sum) * 10;
    }

    void autoSaveRoutes() {
        saveToFile(routeFile);
    }

    void autoSaveBookings() {
        saveBookings(bookingFile);
    }

public:
    FlightSystem() : nextBookingId(1000), routeFile("route_data.txt"),
                     bookingFile("bookings.txt") {}

    void addCity(string city) {
        if (graph.find(city) == graph.end()) {
            graph[city] = vector<Flight>();
            cityTrie.insert(city);
        }
    }

    void addFlight(string src, string dest, int dist, int time, int fare, string flightNum) {
        addCity(src);
        addCity(dest);
        Flight f;
        f.dest = dest;
        f.dist = dist;
        f.time = time;
        f.fare = fare;
        f.flightNum = flightNum;
        graph[src].push_back(f);

        autoSaveRoutes();
    }

    void removeFlight(string src, string dest, string flightNum) {
        if (graph.find(src) == graph.end()) return;

        vector<Flight>& flights = graph[src];
        vector<Flight> newFlights;
        for (size_t i = 0; i < flights.size(); i++) {
            if (!(flights[i].dest == dest && flights[i].flightNum == flightNum)) {
                newFlights.push_back(flights[i]);
            }
        }
        flights = newFlights;

        autoSaveRoutes();
    }

    vector<string> getCitySuggestions(string prefix) {
        return cityTrie.autoComplete(prefix);
    }

    pair<int, vector<string> > dijkstraFastest(string src, string dest) {
        vector<string> emptyPath;
        if (graph.find(src) == graph.end() || graph.find(dest) == graph.end()) {
            return make_pair(-1, emptyPath);
        }

        map<string, int> dist;
        map<string, string> parent;
        priority_queue<pair<int, string>, vector<pair<int, string> >,
                      greater<pair<int, string> > > pq;

        for (map<string, vector<Flight> >::iterator it = graph.begin();
             it != graph.end(); ++it) {
            dist[it->first] = INT_MAX;
        }

        dist[src] = 0;
        pq.push(make_pair(0, src));

        while (!pq.empty()) {
            pair<int, string> top = pq.top();
            int d = top.first;
            string u = top.second;
            pq.pop();

            if (d > dist[u]) continue;

            vector<Flight>& flights = graph[u];
            for (size_t i = 0; i < flights.size(); i++) {
                Flight& flight = flights[i];
                int newDist = dist[u] + flight.time;
                if (newDist < dist[flight.dest]) {
                    dist[flight.dest] = newDist;
                    parent[flight.dest] = u;
                    pq.push(make_pair(newDist, flight.dest));
                }
            }
        }

        if (dist[dest] == INT_MAX) return make_pair(-1, emptyPath);

        vector<string> path;
        string curr = dest;
        while (curr != src) {
            path.push_back(curr);
            curr = parent[curr];
        }
        path.push_back(src);
        reverse(path.begin(), path.end());

        return make_pair(dist[dest], path);
    }

    pair<int, vector<string> > bellmanFordCheapest(string src, string dest) {
        vector<string> emptyPath;
        if (graph.find(src) == graph.end() || graph.find(dest) == graph.end()) {
            return make_pair(-1, emptyPath);
        }

        map<string, int> cost;
        map<string, string> parent;

        for (map<string, vector<Flight> >::iterator it = graph.begin();
             it != graph.end(); ++it) {
            cost[it->first] = INT_MAX;
        }

        cost[src] = 0;
        int n = graph.size();

        for (int i = 0; i < n - 1; i++) {
            for (map<string, vector<Flight> >::iterator it = graph.begin();
                 it != graph.end(); ++it) {
                string city = it->first;
                vector<Flight>& flights = it->second;

                if (cost[city] == INT_MAX) continue;

                for (size_t j = 0; j < flights.size(); j++) {
                    Flight& flight = flights[j];
                    int newCost = cost[city] + flight.fare;
                    if (newCost < cost[flight.dest]) {
                        cost[flight.dest] = newCost;
                        parent[flight.dest] = city;
                    }
                }
            }
        }

        if (cost[dest] == INT_MAX) return make_pair(-1, emptyPath);

        vector<string> path;
        string curr = dest;
        while (curr != src) {
            path.push_back(curr);
            curr = parent[curr];
        }
        path.push_back(src);
        reverse(path.begin(), path.end());

        return make_pair(cost[dest], path);
    }

    pair<int, vector<string> > aStarSearch(string src, string dest) {
        vector<string> emptyPath;
        if (graph.find(src) == graph.end() || graph.find(dest) == graph.end()) {
            return make_pair(-1, emptyPath);
        }

        map<string, int> gScore, fScore;
        map<string, string> parent;
        priority_queue<pair<int, string>, vector<pair<int, string> >,
                      greater<pair<int, string> > > pq;

        for (map<string, vector<Flight> >::iterator it = graph.begin();
             it != graph.end(); ++it) {
            gScore[it->first] = INT_MAX;
            fScore[it->first] = INT_MAX;
        }

        gScore[src] = 0;
        fScore[src] = heuristic(src, dest);
        pq.push(make_pair(fScore[src], src));

        while (!pq.empty()) {
            pair<int, string> top = pq.top();
            int f = top.first;
            string u = top.second;
            pq.pop();

            if (u == dest) break;
            if (f > fScore[u]) continue;

            vector<Flight>& flights = graph[u];
            for (size_t i = 0; i < flights.size(); i++) {
                Flight& flight = flights[i];
                int tentativeG = gScore[u] + flight.time + flight.dist / 10;
                if (tentativeG < gScore[flight.dest]) {
                    parent[flight.dest] = u;
                    gScore[flight.dest] = tentativeG;
                    fScore[flight.dest] = tentativeG + heuristic(flight.dest, dest);
                    pq.push(make_pair(fScore[flight.dest], flight.dest));
                }
            }
        }

        if (gScore[dest] == INT_MAX) return make_pair(-1, emptyPath);

        vector<string> path;
        string curr = dest;
        while (curr != src) {
            path.push_back(curr);
            curr = parent[curr];
        }
        path.push_back(src);
        reverse(path.begin(), path.end());

        return make_pair(gScore[dest], path);
    }

    vector<pair<string, string> > bfsAllPaths(string src) {
        vector<pair<string, string> > reachable;
        if (graph.find(src) == graph.end()) return reachable;

        queue<string> q;
        set<string> visited;
        q.push(src);
        visited.insert(src);

        while (!q.empty()) {
            string u = q.front();
            q.pop();

            vector<Flight>& flights = graph[u];
            for (size_t i = 0; i < flights.size(); i++) {
                Flight& flight = flights[i];
                if (visited.find(flight.dest) == visited.end()) {
                    visited.insert(flight.dest);
                    q.push(flight.dest);
                    reachable.push_back(make_pair(u, flight.dest));
                }
            }
        }
        return reachable;
    }

    void dfsUtil(string u, set<string>& visited, vector<string>& component) {
        visited.insert(u);
        component.push_back(u);

        if (graph.find(u) != graph.end()) {
            vector<Flight>& flights = graph[u];
            for (size_t i = 0; i < flights.size(); i++) {
                Flight& flight = flights[i];
                if (visited.find(flight.dest) == visited.end()) {
                    dfsUtil(flight.dest, visited, component);
                }
            }
        }
    }

    vector<vector<string> > getConnectedComponents() {
        set<string> visited;
        vector<vector<string> > components;

        for (map<string, vector<Flight> >::iterator it = graph.begin();
             it != graph.end(); ++it) {
            string city = it->first;
            if (visited.find(city) == visited.end()) {
                vector<string> component;
                dfsUtil(city, visited, component);
                components.push_back(component);
            }
        }
        return components;
    }

    vector<Flight> getNextFlights(string src, int count) {
        vector<Flight> empty;
        if (graph.find(src) == graph.end()) return empty;

        vector<Flight> flights = graph[src];
        if ((int)flights.size() <= count) return flights;

        mergeSort(flights, 0, flights.size() - 1, 2);
        return vector<Flight>(flights.begin(), flights.begin() + count);
    }

    void sortFlights(string src, int mode) {
        if (graph.find(src) == graph.end()) {
            cout << "City not found!\n";
            return;
        }

        vector<Flight>& flights = graph[src];
        mergeSort(flights, 0, flights.size() - 1, mode);

        cout << "\nSorted Flights from " << src << ":\n";
        cout << string(80, '-') << "\n";
        for (size_t i = 0; i < flights.size(); i++) {
            Flight& f = flights[i];
            cout << "To: " << f.dest << " | Flight: " << f.flightNum
                 << " | Fare: Rs" << f.fare << " | Time: " << f.time
                 << "min | Dist: " << f.dist << "km\n";
        }
    }

    int bookTicket(string passenger, string route, int fare) {
        char seatLetter = 'A' + (nextBookingId % 6);
        int seatNum = 1 + (nextBookingId % 30);
        stringstream ss;
        ss << seatNum << seatLetter;
        string seat = ss.str();

        Booking b;
        b.id = nextBookingId;
        b.passenger = passenger;
        b.route = route;
        b.fare = fare;
        b.seat = seat;

        bookings.addBooking(b);

        autoSaveBookings();

        return nextBookingId++;
    }

    bool cancelTicket(int id) {
        if (bookings.findBooking(id)) {
            bookings.cancelBooking(id);

            autoSaveBookings();

            return true;
        }
        return false;
    }

    void listAllBookings() {
        vector<Booking> all = bookings.getAllBookings();
        if (all.empty()) {
            cout << "No bookings found.\n";
            return;
        }

        cout << "\n" << string(90, '=') << "\n";
        cout << "ALL BOOKINGS\n";
        cout << string(90, '=') << "\n";
        for (size_t i = 0; i < all.size(); i++) {
            Booking& b = all[i];
            cout << "ID: " << b.id << " | Passenger: " << b.passenger
                 << " | Route: " << b.route << " | Fare: Rs" << b.fare
                 << " | Seat: " << b.seat << "\n";
        }
        cout << string(90, '=') << "\n";
    }

    void exportGraphDOT(string filename) {
        ofstream file(filename.c_str());
        file << "digraph FlightRoutes {\n";
        file << "  rankdir=LR;\n";
        file << "  node [shape=circle, style=filled, color=lightblue];\n";

        for (map<string, vector<Flight> >::iterator it = graph.begin();
             it != graph.end(); ++it) {
            string city = it->first;
            vector<Flight>& flights = it->second;
            for (size_t i = 0; i < flights.size(); i++) {
                Flight& f = flights[i];
                file << "  \"" << city << "\" -> \"" << f.dest
                     << "\" [label=\"" << f.flightNum << "\\nRs" << f.fare
                     << "\\n" << f.time << "min\"];\n";
            }
        }
        file << "}\n";
        file.close();
        cout << "Graph exported to " << filename << "\n";
    }

    void loadFromFile(string filename) {
        ifstream file(filename.c_str());
        if (!file.is_open()) {
            cout << "No existing route data. Starting fresh.\n";
            return;
        }

        string line;
        int count = 0;
        while (getline(file, line)) {
            stringstream ss(line);
            string src, dest, flightNum;
            int dist, time, fare;
            if (ss >> src >> dest >> dist >> time >> fare >> flightNum) {
                addCity(src);
                addCity(dest);
                Flight f;
                f.dest = dest;
                f.dist = dist;
                f.time = time;
                f.fare = fare;
                f.flightNum = flightNum;
                graph[src].push_back(f);
                count++;
            }
        }
        file.close();
        cout << "Loaded " << count << " routes from " << filename << "\n";
    }

    void saveToFile(string filename) {
        ofstream file(filename.c_str());
        int count = 0;
        for (map<string, vector<Flight> >::iterator it = graph.begin();
             it != graph.end(); ++it) {
            string city = it->first;
            vector<Flight>& flights = it->second;
            for (size_t i = 0; i < flights.size(); i++) {
                Flight& f = flights[i];
                file << city << " " << f.dest << " " << f.dist << " "
                     << f.time << " " << f.fare << " " << f.flightNum << "\n";
                count++;
            }
        }
        file.close();
    }

    void loadBookings(string filename) {
        ifstream file(filename.c_str());
        if (!file.is_open()) {
            cout << "No existing bookings. Starting fresh.\n";
            return;
        }

        string line;
        int count = 0;
        while (getline(file, line)) {
            stringstream ss(line);
            int id, fare;
            string passenger, route, seat;
            char delim;

            if (ss >> id >> delim) {
                getline(ss, passenger, '|');
                getline(ss, route, '|');
                ss >> fare >> delim;
                getline(ss, seat);

                size_t start = passenger.find_first_not_of(" ");
                size_t end = passenger.find_last_not_of(" ");
                if (start != string::npos)
                    passenger = passenger.substr(start, end - start + 1);

                start = route.find_first_not_of(" ");
                end = route.find_last_not_of(" ");
                if (start != string::npos)
                    route = route.substr(start, end - start + 1);

                start = seat.find_first_not_of(" ");
                end = seat.find_last_not_of(" ");
                if (start != string::npos)
                    seat = seat.substr(start, end - start + 1);

                Booking b;
                b.id = id;
                b.passenger = passenger;
                b.route = route;
                b.fare = fare;
                b.seat = seat;

                bookings.addBooking(b);
                if (id >= nextBookingId) nextBookingId = id + 1;
                count++;
            }
        }
        file.close();
        cout << "Loaded " << count << " bookings from " << filename << "\n";
    }

    void saveBookings(string filename) {
        ofstream file(filename.c_str());
        vector<Booking> all = bookings.getAllBookings();
        for (size_t i = 0; i < all.size(); i++) {
            Booking& b = all[i];
            file << b.id << " | " << b.passenger << " | " << b.route
                 << " | " << b.fare << " | " << b.seat << "\n";
        }
        file.close();
    }

    void displayMenu() {
        cout << "\n" << string(60, '=') << "\n";
        cout << " INTELLIGENT FLIGHT ROUTE OPTIMIZER\n";
        cout << string(60, '=') << "\n";
        cout << " 1. Add Flight Route\n";
        cout << " 2. Remove Flight Route\n";
        cout << " 3. Find Fastest Route (Dijkstra)\n";
        cout << " 4. Find Cheapest Route (Bellman-Ford)\n";
        cout << " 5. Smart Route Search (A*)\n";
        cout << " 6. City Autocomplete Search\n";
        cout << " 7. Check Connectivity (BFS)\n";
        cout << " 8. Find Connected Components (DFS)\n";
        cout << " 9. View Next Flights (Priority Queue)\n";
        cout << "10. Sort Flights\n";
        cout << "11. Book Ticket\n";
        cout << "12. Cancel Ticket\n";
        cout << "13. List All Bookings\n";
        cout << "14. Export Graph (DOT format)\n";
        cout << "15. Save & Exit\n";
        cout << string(60, '=') << "\n";
        cout << "Enter choice: ";
    }

    void displayStats() {
        cout << "\nSystem Stats:\n";
        cout << "   Cities: " << graph.size() << "\n";
        int totalRoutes = 0;
        for (map<string, vector<Flight> >::iterator it = graph.begin();
             it != graph.end(); ++it) {
            totalRoutes += it->second.size();
        }
        cout << "   Routes: " << totalRoutes << "\n";
        cout << "   Bookings: " << bookings.getAllBookings().size() << "\n\n";
    }
};

int main() {
    FlightSystem system;

    cout << "\nFLIGHT ROUTE OPTIMIZER\n";
    cout << "Loading data from files...\n";
    system.loadFromFile("route_data.txt");
    system.loadBookings("bookings.txt");
    system.displayStats();

    int choice;
    bool running = true;

    while (running) {
        system.displayMenu();
        cin >> choice;
        cin.ignore();

        switch (choice) {
            case 1: {
                string src, dest, flightNum;
                int dist, time, fare;
                cout << "Source city: "; getline(cin, src);
                cout << "Destination city: "; getline(cin, dest);
                cout << "Distance (km): "; cin >> dist;
                cout << "Time (minutes): "; cin >> time;
                cout << "Fare (Rs): "; cin >> fare;
                cin.ignore();
                cout << "Flight number: "; getline(cin, flightNum);
                system.addFlight(src, dest, dist, time, fare, flightNum);
                cout << "Flight added and saved!\n";
                break;
            }
            case 2: {
                string src, dest, flightNum;
                cout << "Source city: "; getline(cin, src);
                cout << "Destination city: "; getline(cin, dest);
                cout << "Flight number: "; getline(cin, flightNum);
                system.removeFlight(src, dest, flightNum);
                cout << "Flight removed and saved!\n";
                break;
            }
            case 3: {
                string src, dest;
                cout << "From: "; getline(cin, src);
                cout << "To: "; getline(cin, dest);
                pair<int, vector<string> > result = system.dijkstraFastest(src, dest);
                if (result.first == -1) {
                    cout << "No route found!\n";
                } else {
                    cout << "\nFASTEST ROUTE (Dijkstra)\n";
                    cout << "Time: " << result.first << " minutes\n";
                    cout << "Path: ";
                    for (size_t i = 0; i < result.second.size(); i++) {
                        cout << result.second[i];
                        if (i < result.second.size() - 1) cout << " -> ";
                    }
                    cout << "\n";
                }
                break;
            }
            case 4: {
                string src, dest;
                cout << "From: "; getline(cin, src);
                cout << "To: "; getline(cin, dest);
                pair<int, vector<string> > result = system.bellmanFordCheapest(src, dest);
                if (result.first == -1) {
                    cout << "No route found!\n";
                } else {
                    cout << "\nCHEAPEST ROUTE (Bellman-Ford)\n";
                    cout << "Cost: Rs" << result.first << "\n";
                    cout << "Path: ";
                    for (size_t i = 0; i < result.second.size(); i++) {
                        cout << result.second[i];
                        if (i < result.second.size() - 1) cout << " -> ";
                    }
                    cout << "\n";
                }
                break;
            }
            case 5: {
                string src, dest;
                cout << "From: "; getline(cin, src);
                cout << "To: "; getline(cin, dest);
                pair<int, vector<string> > result = system.aStarSearch(src, dest);
                if (result.first == -1) {
                    cout << "No route found!\n";
                } else {
                    cout << "\nSMART ROUTE (A* Search)\n";
                    cout << "Score: " << result.first << "\n";
                    cout << "Path: ";
                    for (size_t i = 0; i < result.second.size(); i++) {
                        cout << result.second[i];
                        if (i < result.second.size() - 1) cout << " -> ";
                    }
                    cout << "\n";
                }
                break;
            }
            case 6: {
                string prefix;
                cout << "Enter city prefix: "; getline(cin, prefix);
                vector<string> suggestions = system.getCitySuggestions(prefix);
                if (suggestions.empty()) {
                    cout << "No cities found.\n";
                } else {
                    cout << "\nSuggestions:\n";
                    for (size_t i = 0; i < suggestions.size(); i++) {
                        cout << "   " << suggestions[i] << "\n";
                    }
                }
                break;
            }
            case 7: {
                string src;
                cout << "Source city: "; getline(cin, src);
                vector<pair<string, string> > paths = system.bfsAllPaths(src);
                if (paths.empty()) {
                    cout << "No reachable cities.\n";
                } else {
                    cout << "\nReachable destinations:\n";
                    for (size_t i = 0; i < paths.size(); i++) {
                        cout << "   " << paths[i].first << " -> " << paths[i].second << "\n";
                    }
                }
                break;
            }
           case 8: {
                vector<vector<string> > components = system.getConnectedComponents();
                cout << "\nConnected Components: " << components.size() << "\n";
                for (size_t i = 0; i < components.size(); i++) {
                    cout << "Component " << (i + 1) << ": ";
                    for (size_t j = 0; j < components[i].size(); j++) {
                        cout << components[i][j] << " ";
                    }
                    cout << "\n";
                }
                break;
            }
            case 9: {
                string src;
                int count;
                cout << "Source city: "; getline(cin, src);
                cout << "Number of flights: "; cin >> count;
                vector<Flight> flights = system.getNextFlights(src, count);
                if (flights.empty()) {
                    cout << "No flights available.\n";
                } else {
                    cout << "\nNext " << flights.size() << " flights:\n";
                    for (size_t i = 0; i < flights.size(); i++) {
                        Flight& f = flights[i];
                        cout << "   " << f.flightNum << " -> " << f.dest
                             << " (Rs" << f.fare << ", " << f.time << "min)\n";
                    }
                }
                break;
            }
            case 10: {
                string src;
                int mode;
                cout << "Source city: "; getline(cin, src);
                cout << "Sort by (1=Fare, 2=Time, 3=Distance): "; cin >> mode;
                system.sortFlights(src, mode);
                break;
            }
            case 11: {
                string passenger, route;
                int fare;
                cout << "Passenger name: "; getline(cin, passenger);
                cout << "Route (e.g., Delhi->Mumbai): "; getline(cin, route);
                cout << "Fare: Rs"; cin >> fare;
                int id = system.bookTicket(passenger, route, fare);
                cout << "Ticket booked! Booking ID: " << id << " (Auto-saved)\n";
                break;
            }
            case 12: {
                int id;
                cout << "Booking ID: "; cin >> id;
                if (system.cancelTicket(id)) {
                    cout << "Booking cancelled! (Auto-saved)\n";
                } else {
                    cout << "Booking not found!\n";
                }
                break;
            }
            case 13: {
                system.listAllBookings();
                break;
            }
            case 14: {
                system.exportGraphDOT("routes.dot");
                cout << "see the generated word file routes.dot \n";
                break;
            }
            case 15: {
                cout << "\nAll data already saved automatically. Goodbye!\n";
                running = false;
                break;
            }
            default:
                cout << "Invalid choice!\n";
        }
    }

    return 0;
}
