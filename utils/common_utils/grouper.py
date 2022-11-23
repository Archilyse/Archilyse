from typing import Hashable, List, Set


class Grouper:
    """
    Groups elements that are linked and have transitive property,
    meaning if a is linked to b, and b is linked to c, then a is linked to c.
    Example:
       Having the following groups:
         {a, b} {c,d} {e,f,g}
       linking a and c would result in:
         {a,b,c,d} {e,f,g}
    """

    def __init__(self):
        self.groups: List[Set] = []

    def link(self, a: Hashable, b: Hashable) -> None:
        candidates = [
            i for i, group in enumerate(self.groups) if any(x in group for x in (a, b))
        ]
        if not candidates:
            self.groups.append({a, b})
        else:
            self.groups[candidates[0]].update({a, b})
            if len(candidates) > 1:  # 2 groups need merging
                self.groups[candidates[0]].update(self.groups.pop(candidates[1]))
