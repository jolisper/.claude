# Refactoring Rules

---

## Rule 10: Replace Constructor with Factory Method

*Sources:*
- *Joshua Bloch, Effective Java (3rd ed.), Item 1 — "Consider static factory methods instead of constructors"*
- *Martin Fowler, Refactoring catalog — "Replace Constructor with Factory Function"*

> "A class constructor can only return an instance of the class itself. A static factory method can return an instance of a subclass, a cached instance, or communicate intent through its name."
> — Bloch, paraphrased

Bare `new` calls have three problems:
1. **No name** — `new Employee(2)` tells you nothing; `Employee.createEngineer()` does
2. **No flexibility** — a constructor always returns exactly `ClassName`; a factory can return a subtype or a cached instance
3. **Construction logic leaks** — callers must know which arguments produce which kind of object

**When to apply**: when `new` is called with a type code, a flag, or a combination of arguments that selects between meaningfully different objects — replace with a named factory method that communicates the intent.

**Mechanics:**
1. Create a static factory method that delegates to the constructor
2. Replace all call sites with the factory method
3. Optionally make the constructor private to enforce use of the factory

**Before:**
```java
leadEngineer = new Employee(document.leadEngineer, "E");
manager = new Employee(document.manager, "M");
```

**After:**
```java
leadEngineer = Employee.createEngineer(document.leadEngineer);
manager = Employee.createManager(document.manager);

// inside Employee:
static Employee createEngineer(String name) {
    return new Employee(name, "E");
}
static Employee createManager(String name) {
    return new Employee(name, "M");
}
```

**Common factory naming conventions** (Bloch, Item 1):

| Name | Meaning |
|---|---|
| `of(...)` | aggregation — takes multiple params, returns an instance |
| `from(...)` | type conversion — takes one param of a different type |
| `valueOf(...)` | verbose alternative to `of` / `from` |
| `create()` / `newInstance()` | guarantees a fresh instance each time |
| `getInstance()` | may return a cached instance |
| `getType()` / `createType()` | factory on a different class (e.g. `Files.newInputStream()`) |

---

## Rule 11: Decompose Conditional

*Source: Martin Fowler, Refactoring Ch. 7 — Decompose Conditional*

> "You have a complicated conditional (if-then-else) statement. Extract methods from the condition, then part, and else parts."

The problem with complex conditionals is that the code tells you *what* happens but obscures *why*. Extracting the condition and each branch into named methods replaces the statement of what you are doing with why you are doing it — the method name reads more like a comment.

**Mechanics:**
1. Extract the condition into its own method
2. Extract the 'then part' and 'else part' into their own methods

**Before:**
```java
if (date.before(SUMMER_START) || date.after(SUMMER_END))
    charge = quantity * _winterRate + _winterServiceCharge;
else charge = quantity * _summerRate;
```

**After:**
```java
if (notSummer(date))
    charge = winterCharge(quantity);
else charge = summerCharge(quantity);

private boolean notSummer(Date date) {
    return date.before(SUMMER_START) || date.after(SUMMER_END);
}
private double winterCharge(int quantity) {
    return quantity * _winterRate + _winterServiceCharge;
}
private double summerCharge(int quantity) {
    return quantity * _summerRate;
}
```

---

## Rule 11: Consolidate Conditional Expression

*Source: Martin Fowler, Refactoring Ch. 7 — Consolidate Conditional Expression*

> "You have a sequence of conditional tests with the same result. Combine them into a single conditional expression, and extract it."

When several checks all lead to the same outcome, they represent a single logical condition. Consolidating them into one named method makes the intent explicit and sets you up to apply Decompose Conditional.

**Before:**
```java
double disabilityAmount() {
    if (_seniority < 2) return 0;
    if (_monthsDisabled > 12) return 0;
    if (_isPartTime) return 0;
    // compute the disability amount
}
```

**After:**
```java
double disabilityAmount() {
    if (isEligibleForDisability()) return 0;
    // compute the disability amount
}

private boolean isEligibleForDisability() {
    return (_seniority < 2) || (_monthsDisabled > 12) || (_isPartTime);
}
```

---

# Object Calisthenics — 9 Rules by Jeff Bay

Source: *ThoughtWorks Anthology*, Pragmatic Programmers

---

## Rule 1: One level of indentation per method

Each method must do exactly one thing — one control structure or one block of statements. If you have nested control structures, you are working at multiple levels of abstraction, which means you are doing more than one thing.

**Technique**: Use Extract Method to pull out behaviors until methods have only one level of indentation.

**Before:**
```java
String board() {
    StringBuffer buf = new StringBuffer();
    for (int i = 0; i < 10; i++) {
        for (int j = 0; j < 10; j++)
            buf.append(data[i][j]);
        buf.append("\n");
    }
    return buf.toString();
}
```

**After:**
```java
String board() {
    StringBuffer buf = new StringBuffer();
    collectRows(buf);
    return buf.toString();
}

void collectRows(StringBuffer buf) {
    for (int i = 0; i < 10; i++)
        collectRow(buf, i);
}

void collectRow(StringBuffer buf, int row) {
    for (int i = 0; i < 10; i++)
        buf.append(data[row][i]);
    buf.append("\n");
}
```

---

## Rule 2: Don't use the ELSE keyword

Conditionals are a frequent source of duplication and complexity. Object-oriented languages provide polymorphism for handling conditional cases. Removing `else` forces you to find better solutions.

**Techniques**: early return (guard clauses), Null Object pattern, polymorphism, strategy pattern.

**Before:**
```java
if (status == DONE) {
    doSomething();
} else {
    doSomethingElse();
}
```

**After (guard clause):**
```java
if (status == DONE) {
    doSomething();
    return;
}
doSomethingElse();
```

---

## Rule 3: Wrap all primitives and Strings

A primitive on its own is just a scalar — it has no meaning. Wrapping it in a small object gives both the compiler and the programmer additional information about what the value is and why it is being used. It also provides an obvious home for behavior related to that value.

**Example**: Instead of `int hour`, use `Hour hour`. Instead of `String email`, use `Email email`. The compiler then prevents passing a `Year` where an `Hour` is expected.

---

## Rule 4: First class collections

Any class that contains a collection should contain no other member variables. Each collection gets wrapped in its own class. Behaviors related to the collection (filtering, joining, applying rules) belong in this new class.

**Before:**
```java
class Order {
    List<Item> items;
    String customerName;  // violates this rule
}
```

**After:**
```java
class Order {
    Items items;  // Items is a first-class collection
    CustomerName customerName;
}

class Items {
    List<Item> items;
    // filtering, totaling, etc. live here
}
```

---

## Rule 5: One dot per line

If you have more than one dot on a line, the activity is happening in the wrong place. Multiple dots mean your object is either:
- A middleman that knows too much about too many people (move the activity into one of the other objects), or
- Digging deeply into another object's internals (violating encapsulation).

**Law of Demeter**: Only talk to your immediate friends. You can play with your toys, toys that you make, and toys that someone gives you — never with your toy's toys.

**Before:**
```java
buf.append(l.current.representation.substring(0, 1));
```

**After:**
```java
l.addTo(buf);  // each object handles its own concern
```

---

## Rule 6: Don't abbreviate

Abbreviations are confusing and hide larger problems. If you want to abbreviate because you're typing the same word repeatedly, perhaps the method is used too heavily and you're missing opportunities to reduce duplication. If names are getting long, it may signal a misplaced responsibility or a missing class.

- Keep class and method names to 1–2 words
- Avoid names that duplicate the context: if the class is `Order`, the method should be `ship()` not `shipOrder()`

---

## Rule 7: Keep all entities small

- No class over **50 lines**
- No package over **10 files**

Classes over 50 lines usually do more than one thing. 50-line classes fit on one screen without scrolling, making them easier to grasp quickly. Use packages to group cohesive clusters of small classes that work together toward a goal.

---

## Rule 8: No classes with more than two instance variables

Adding a new instance variable immediately decreases cohesion. Two kinds of classes are acceptable:
- Classes that maintain the state of a single instance variable
- Classes that coordinate two separate variables

Do not mix the two kinds.

**Before:**
```java
class Name {
    String first;
    String middle;
    String last;
}
```

**After:**
```java
class Name {
    Surname family;
    GivenNames given;
}

class Surname {
    String family;
}

class GivenNames {
    List<String> names;
}
```

---

## Rule 9: No getters/setters/properties

If objects encapsulate the appropriate instance variables but behavior still doesn't follow, you are violating encapsulation through getters and setters. When external code can ask for a value, the behavior stays where the asking happens instead of where the data lives.

**Principle**: **Tell, don't ask.** Tell objects to do things for you rather than asking for their data and doing it yourself.

**Before:**
```java
int amount = money.getAmount();
String currency = money.getCurrency();
// ... logic using amount and currency lives here
```

**After:**
```java
money.add(other);       // Money knows how to add itself
money.format(printer);  // Money knows how to print itself
```
