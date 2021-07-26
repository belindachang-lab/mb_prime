from abc import ABC
from typing import Any, List, Tuple, Dict, Iterable, Union

from infinity import Infinity

from hetero_spacer_generator.primer_types import SimpleCriterion
from hetero_spacer_generator.sequence_tools import get_max_complementarity, \
    get_max_complementarity_consec
from Bio.Seq import Seq
import spacer_generator.spacer_filters as spf

FORWARD = "forward"
REVERSE = "reverse"
TAB = '    '

DEFAULT_PS_TYPE = 'pai'
PAIRWISE = 'pai'
SIMULTANEOUS = 'sim'

POSSIBLE_PAIRINGS = spf.get_all_arrangements(4, 4)

# Lower values make variance a more important variable in score calculation
# decisions
VARIANCE_IMPORTANCE = 3


class Primer(Seq):
    """Basic methods common among all primers"""

    def __init__(self, seq: str):
        super().__init__(seq)


class MBPrimer(Primer):
    """Stores the attributes of a primer used in two step PCR for metabarcoding.

    === Private Attributes ===
    _adapter_seq:
            The adapter region of the primer.
    _index_seq:
            The indexing region.
    _heterogen_seq:
            The heterogeneity sequence of the primer.
    _binding_seq:
            The specific binding region.
    _direction:
            Primers are either "forward" or "reverse".

    On Directionality:
            The sequence of the primer will be given in the 5'-3' direction.
    """
    _adapter_seq: Seq
    _index_seq: Seq
    _heterogen_seq: Seq
    _binding_seq: Seq
    _direction: str

    def __init__(self, adapter_seq: str, index_seq: str, heterogen_seq: str,
                 primer_region: str) -> None:
        """Constructs a primer sequence with components in the following order:
        <adapter_seq> <index_seq> <heterogen_seq> <primer_region> with each of
        their sequences read left to right."""
        super().__init__(''.join([adapter_seq, index_seq, heterogen_seq,
                                  primer_region]))

        self._adapter_seq = Seq(adapter_seq)
        self._index_seq = Seq(index_seq)
        self._heterogen_seq = Seq(heterogen_seq)
        self._binding_seq = Seq(primer_region)

    def get_adapter_seq(self) -> Seq:
        """Returns adapter_seq."""
        return self._adapter_seq

    def get_index_seq(self) -> Seq:
        """Returns index_seq."""
        return self._index_seq

    def get_heterogen_seq(self) -> Seq:
        """Returns heterogen_seq."""
        return self._heterogen_seq

    def get_binding_seq(self) -> Seq:
        """Returns binding_seq."""
        return self._binding_seq


class MBPrimerBuilder:
    """Stores the attributes of a primer used in two step PCR for metabarcoding.

    === Private Attributes ===
    _adapter_seq:
            The adapter region of the primer.
    _index_seq:
            The indexing region.
    _heterogen_seq:
            The heterogeneity sequence of the primer.
    _binding_seq:
            The locus specific binding region.
    _direction:
            Primers are either "forward" or "reverse".

    On Directionality:
            The sequence of the primer will be given in the 5'-3' direction.
    """
    _adapter_seq: Seq
    _index_seq: Seq
    _heterogen_seq: Seq
    _binding_seq: Seq

    def set_adapter_seq(self, seq: Union[Seq, str]) -> None:
        """Sets adapter_seq to <seq>."""
        self._adapter_seq = Seq(str(seq))

    def set_index_seq(self, seq: Union[Seq, str]) -> None:
        """Sets index_seq to <seq>."""
        self._index_seq = Seq(str(seq))

    def set_heterogen_seq(self, seq: Union[Seq, str]) -> None:
        """Sets heterogen_seq to <seq>."""
        self._heterogen_seq = Seq(str(seq))

    def set_binding_seq(self, seq: Union[Seq, str]) -> None:
        """Sets binding_seq to <seq>."""
        self._binding_seq = Seq(str(seq))

    def get_adapter_seq(self) -> Seq:
        """Returns adapter_seq."""
        return self._adapter_seq

    def get_index_seq(self) -> Seq:
        """Returns index_seq."""
        return self._index_seq

    def get_heterogen_seq(self) -> Seq:
        """Returns heterogen_seq."""
        return self._heterogen_seq

    def get_binding_seq(self) -> Seq:
        """Returns binding_seq."""
        return self._binding_seq

    def get_MBPrimer(self) -> MBPrimer:
        """Returns a completed version of this primer."""
        return MBPrimer(self._adapter_seq.__str__(),
                        self._index_seq.__str__(),
                        self._heterogen_seq.__str__(),
                        self._binding_seq.__str__())


def spacers_to_primers(incomplete_primer: MBPrimerBuilder,
                       spacers: Tuple[Seq, Seq, Seq, Seq]) -> List[MBPrimer]:
    """Completes the <incomplete_primer> with each of <spacers> and returns  a
    list of the results."""
    primers = []
    for spacer in spacers:
        incomplete_primer.set_heterogen_seq(spacer)
        primers.append(incomplete_primer.get_MBPrimer())
    return primers


def eval_total_complementarity(incomplete_primer: MBPrimerBuilder,
                               spacers: Tuple[Seq, Seq, Seq, Seq]) -> int:
    """Returns the max complementarity between any of <spacers> and any
    <incomplete_primer> completed with a spacer in <spacers>."""
    cmplmnt_lst = []
    primers = spacers_to_primers(incomplete_primer, spacers)
    for spacer in spacers:
        # Calculate max_comp for any forward primer and forward hetero.
        rev_hetero = spacer.__str__()[::-1]
        cmplmnt_lst.append(get_max_complementarity(Seq(rev_hetero),
                                                   primers))
        # No need to reverse hetero seq when calculating binding to reverse
        # primer.
    return max(cmplmnt_lst)


def eval_consecutive_complementarity(incomplete_primer: MBPrimerBuilder,
                                     spacers: Tuple[Seq, Seq, Seq, Seq]) -> int:
    """Returns the max complementarity between any of <spacers> and any
    <incomplete_primer> completed with a spacer in <spacers>."""
    cmplmnt_lst = []
    primers = spacers_to_primers(incomplete_primer, spacers)
    for spacer in spacers:
        # Calculate max_comp for any forward primer and forward hetero.
        rev_hetero = spacer.__str__()[::-1]
        cmplmnt_lst.append(get_max_complementarity_consec(Seq(rev_hetero),
                                                          primers))
        # No need to reverse hetero seq when calculating binding to reverse
        # primer.
    return max(cmplmnt_lst)


def remove_highest_scores(lst: List[Any], scores_dict: Dict[int, List[int]],
                          num_to_keep: int, lowest: bool = False) -> None:
    """Given <scores_dict> which maps scores to a list of indices, removes items
    at all indices in <lst> except for the <num_to_keep> highest scoring items.
    Iff <lowest> is true, then this behaviour is reversed, and the lowest
    scoring items will be kept."""
    best_to_worst = []
    sorted_keys = list(scores_dict.keys())
    sorted_keys.sort()
    # Insert indices such that best_to_worse contains indices in the
    # lowest scoring -> highest scoring direction
    for key in sorted_keys:
        for index in scores_dict[key]:
            best_to_worst.append(index)

    # Score preference is reversed if lower scores are preferred.
    if lowest:
        best_to_worst.reverse()

    # Remove unwanted items at higher indices first.
    ind_to_remove = best_to_worst[num_to_keep: len(best_to_worst)]
    ind_to_remove.sort(reverse=True)

    for index in ind_to_remove:
        lst.pop(index)


class HalfSet:
    """A set of 4 forward or reverse primers.

    === Public Attributes ===
    primers:
            A set of valid Metabarcoding primers"""

    primers: Tuple[MBPrimer, MBPrimer, MBPrimer, MBPrimer]

    _average_score: float
    _num_scores: int

    _is_active: bool

    def __init__(self, incomplete_primer: MBPrimerBuilder,
                 spacers: Tuple[Seq, Seq, Seq, Seq]) -> None:
        """Constructs a set of primers complete using <incomplete_primer> each
        with one of <spacers>"""
        self._average_score = 0
        self._num_scores = 0
        self._is_active = True
        primers = []
        for spacer in spacers:
            incomplete_primer.set_heterogen_seq(spacer)
            primers.append(incomplete_primer.get_MBPrimer())
        incomplete_primer.set_heterogen_seq(Seq(''))
        self.primers = (primers[0], primers[1], primers[2], primers[3])

    def __iter__(self):
        """Returns an iterator for the set of primers contained in this set."""
        return iter(self.primers)

    def deactivate(self) -> None:
        """Deactivates this HalfSet"""
        self._is_active = False

    def reset_avg(self) -> None:
        """Resets the values associated with calculating this HalfSets avg
        performance."""
        self._average_score = 0
        self._num_scores = 0

    def update_avg_score(self, new_score: Union[int, List[int]]) -> None:
        """Adds <new_score> to this HalfSets running average"""
        if type(new_score) == int:
            self._num_scores += 1
            self._average_score = self._average_score * \
                                  (self._num_scores - 1) / self._num_scores + \
                                  new_score / self._num_scores
        elif type(new_score) == list:
            old_score = self._num_scores
            self._num_scores += len(new_score)
            self._average_score = self._average_score * \
                                  old_score / self._num_scores + \
                                  new_score / self._num_scores

    def get_avg(self) -> float:
        """Returns the average score produced by this HalfSet."""
        return self._average_score


def evaluate_heterogen_binding_cross(forward_primers: HalfSet,
                                     reverse_primers: HalfSet) -> int:
    """Returns the max site complementarity between the heterogeneity
    sequences in <forward_primers> and the <reverse_primers> and visa versa. """
    max_comp = 0

    # Calculate the maximum complementarity between any of the reverse and
    # forward primers
    for primer in forward_primers:
        comp = get_max_complementarity(primer.get_heterogen_seq(),
                                       reverse_primers)
        if comp > max_comp:
            max_comp = comp

    # Same process for reverse primers
    for primer in reverse_primers:
        comp = get_max_complementarity(primer.get_heterogen_seq(),
                                       forward_primers)
        if comp > max_comp:
            max_comp = comp

    return max_comp


class PrimerSet:
    """A set of MBPrimers.
    === Private Attributes ===
    _forward_primers:
            The forward primers contained in this set.
    _reverse_primers:
            The reverse primers contained by this set."""

    _forward_primers: List[MBPrimer]
    _reverse_primers: List[MBPrimer]

    def __init__(self, forward_primers: Iterable[MBPrimer] = (),
                 reverse_primers: Iterable[MBPrimer] = ()) -> None:
        """Initialises the Primer set with the given list of primers."""
        self._forward_primers = []
        self._reverse_primers = []
        for primer in forward_primers:
            self._forward_primers.append(primer)
        for primer in reverse_primers:
            self._reverse_primers.append(primer)

    def __str__(self) -> str:
        """Returns a string representation of this primer set."""
        str_rep = ''
        str_rep += 'Forward Primers:\n'
        for primer in self._forward_primers:
            str_rep += TAB + TAB.join([str(primer.get_adapter_seq()),
                                       str(primer.get_index_seq()),
                                       str(primer.get_heterogen_seq()),
                                       str(primer.get_binding_seq())])
            str_rep += '\n'
        str_rep += 'Reverse Primers:\n'
        for primer in self._reverse_primers:
            str_rep += TAB + TAB.join([str(primer.get_adapter_seq()),
                                       str(primer.get_index_seq()),
                                       str(primer.get_heterogen_seq()),
                                       str(primer.get_binding_seq())])
            str_rep += '\n'
        return str_rep


SpacerPairing = Tuple[int, int, int, int]


def calculate_score(scores: List[int, int, int, int]) -> int:
    """Calculates the average score of <scores>, increasing the score for if
    <scores> has high variance."""
    variance = max(scores) - min(scores)
    avg = sum(scores) / 4
    return int(avg * variance / 3)


class PairwisePrimerSet(PrimerSet):
    """A set of MBPrimers intended to be used in pairs.
    --- Private Attributes ---
    _optimal_pairing:
            A pair of some of this sets forward and reverse primers that have
            minimal hetero-binding. Where the pairs are:
            forward_primers[i] pairs with reverse_primers[optimal_pairing[i]].
    _pairing_scores:
            The scores produced by the given pairings of primers.
    _min_pairing_score:
            The best score produced by any pairing.
    """
    _optimal_pairing: SpacerPairing
    _pairing_scores: Dict[SpacerPairing, int]
    _min_pairing_score: int

    def __init__(self, forward_primers: Iterable[MBPrimer] = (),
                 reverse_primers: Iterable[MBPrimer] = ()) -> None:
        """Initialises the Primer set with the given list of primers."""
        super().__init__(forward_primers, reverse_primers)
        self._optimal_pairing = (0, 1, 2, 3)
        self._pairing_scores = {}
        self._min_pairing_score = 0

        for pairing in POSSIBLE_PAIRINGS:
            self._pairing_scores[pairing] = 0

    def __str__(self) -> str:
        """Returns a string representation of this primer set."""
        str_rep = ''
        str_rep += super().__str__()
        str_rep += "Recommended Pairing:" + \
                   ', '.join(["F1 - R{R1:d}",
                              "F2 - R{R2:d}",
                              "F3 - R{R3:d}",
                              "F4 - R{R4:d}"]).format(
                       R1=self._optimal_pairing[0],
                       R2=self._optimal_pairing[1],
                       R3=self._optimal_pairing[2],
                       R4=self._optimal_pairing[3], )
        return str_rep

    def apply_criteria(self, criteria: List[SimpleCriterion],
                       weights: List[int]) -> int:
        """Calculates the scores for all parings using all of <criteria> and
        weights, returning the minimum of those scores.
        Assumes:
            Each criteria[i] corresponds to weights[i]
            i.e. len(criteria) == len(weights)."""
        for i in range(len(criteria)):
            self.apply_criterion(criteria[i], weights[i])
        return self.update_min_score()

    def update_min_score(self) -> int:
        """Updates <self.min_score> to the minimum score in pairing_scores."""
        self._min_pairing_score = min(self._pairing_scores.values())
        self._optimal_pairing = \
            {v: k for k, v in self._pairing_scores.items()}[
                self._min_pairing_score]
        return self._min_pairing_score

    def apply_criterion(self, criterion: SimpleCriterion, weight: int) -> None:
        """Updates <self.pairing_scores> using <criterion>."""
        for pairing in POSSIBLE_PAIRINGS:
            scores = []
            for i in range(4):
                scores.append(criterion(self._forward_primers[i],
                                        self._reverse_primers[pairing[i]]))
            self._pairing_scores[pairing] += calculate_score(scores) * weight


def co_sort(to_sort: List[int], to_follow: List[Any], reverse: bool = False) \
        -> None:
    """Sorts to_sort least to greatest (greatest to least if reverse is true).
    Whenever an item in to_sort is moved index i to index j, the item in
    to_follow at i is moved to j.

    Precondition:
            len(to_follow) >= len(to_sort)"""
    inv = [-1, 1][reverse]
    for i in range(len(to_sort), 1, -1):
        for j in range(i - 1):
            if to_sort[j] * inv < to_sort[j + 1] * inv:
                to_sort[j], to_sort[j + 1] = to_sort[j + 1], to_sort[j]
                to_follow[j], to_follow[j + 1] = to_follow[j + 1], to_follow[j]


def co_insert(values: List[int], to_follow: List[Any],
              val_to_insert: int, follow_to_insert: Any, reverse: bool = False) \
        -> None:
    """Inserts <val_to_insert> into a the sorted list (L-G) <values> such that
    <values> is still sorted. Will insert <follow_to_insert> into the same index
    in <to_follow> as <val_to_insert> was inserted into <values>."""
    # Used to reverse logic in value comparisons
    dir = 1 - 2 * reverse
    for i in range(len(values)):
        if val_to_insert * dir < values[i] * dir:
            values.insert(i, val_to_insert)
            values.pop()
            to_follow.insert(i, follow_to_insert)
            to_follow.pop()
            return


def add(dic: Dict[Any, List[Any]], key: Any, item: Any) -> None:
    """Adds <item> to the <dic> with <key> if <key> already maps to a list, else
     creates a list at <key> and adds <item> to it."""
    if key in dic.keys():
        dic[key].append(item)
    else:
        dic[key] = [item]


class HeteroSeqTool(ABC):
    """A class that handles heterogeneity spacers.

    --- Private Attributes ---
    _max_spacer_length:
            The maximum length of a spacer produced.
    _num_hetero:
            The length of the heterogeneity that should be ensured across."""

    def __init__(self, max_spacer_length: int, num_hetero: int) -> None:
        """Initialises the attributes to the values specified.
        Precondition:
            max_spacer_length >= num_hetero"""
        self._max_spacer_length = max_spacer_length
        self._num_hetero = num_hetero


def get_n_lowest_matrix(scores: List[List[int]],
                        n: int, highest: bool = False) \
        -> Tuple[List[Tuple[int, int]], List[int]]:
    """Returns a tuple containing: a list of the indices of the <n> lowest
    scores in scores, and a list of those scores. Iff <highest>,
    will return the <n> highest scoring items.

    Assumes:
     - That every score has a correlated item.
     - An item's index in <items> also points to its score in <scores>"""

    # Best scores sorted from lowest to highest complementarity
    min_scores = []
    # The combination of for and rev primers that produced the scores in
    # min_scores.
    min_items = []
    # Set the scores to a list of the worst possible scores
    worst_score = MaxInt() if not highest else - MaxInt()

    rev = -2 * highest + 1

    for i in range(n):
        min_scores.append(worst_score)
        min_items.append((-1, -1))

    # If a score is better than the worst score in scores, replace that
    # score and combo with the better score and combo. Sort best to worst.
    for i in range(len(scores)):
        for j in range(len(scores[i])):
            # Iff highest reverse logic.
            if scores[i][j] * rev < min_scores[-1] * rev:
                co_insert(min_scores, min_items,
                          scores[i][j], (i, j), reverse=highest)

    return min_items, min_scores


def get_n_lowest(scores: List[int], n: int, highest: bool = False) \
        -> Tuple[List[int], List[int]]:
    """Returns a tuple containing [0]: a list of the indices of the <n> lowest
    scores in scores, [1]: a list of those scores. Iff <highest>,
    will return the <n> highest scoring items.

    Assumes:
     - That every score has a correlated item.
     - An item's index in <items> also points to its score in <scores>"""

    # Best scores sorted from lowest to highest complementarity
    min_scores = []
    # The combination of for and rev primers that produced the scores in
    # min_scores.
    min_items = []
    # Set the scores to a list of the worst possible scores
    worst_score = MaxInt() if not highest else - MaxInt()

    rev = -2 * highest + 1

    for i in range(n):
        min_scores.append(worst_score)
        min_items.append(-1)

    # If a score is better than the worst score in scores, replace that
    # score and combo with the better score and combo. Sort best to worst.
    for i in range(len(scores)):
        # Iff highest reverse logic.
        if scores[i] * rev < min_scores[-1] * rev:
            co_insert(min_scores, min_items,
                      scores[i], i, reverse=highest)
            """min_scores[-1] = scores[i][j]
            min_items[-1] = (i, j) 
            co_sort(min_scores, min_items, reverse=highest)"""
            # slow ^

    return min_items, min_scores


def get_these_inds(indices: List[int], values: List[Any]) -> List[Any]:
    """Returns the values in <values> at the indices in <indices>.
    Precondition:
            For every value n in indices, 0 <= n < len(values)"""
    vals = []
    for i in indices:
        vals.append(values[i])
    return vals


def get_these_inds_matrix(indices: List[Tuple[int, int]],
                          values: List[List[Any]]) -> List[Any]:
    """Returns the values in <values> at the indices in <indices>, where
    returned_vals[0] = values[indices[0]][indices[1]]
    Precondition:
            For every value n in indices, 0 <= n < len(values)"""
    vals = []
    for tup in indices:
        vals.append(values[tup[0]][tup[1]])
    return vals


def get_cross_iteration_pattern(num_iter: int) -> List[List[Tuple[int, int]]]:
    """Returns an iteration pattern that, when performed over a square
    matrix, ensures that each column and row is iterated over the once number
    each iteration.
    Usage:
    >>> # Some square matrix, below example just shows symmetry of iteration.
    >>> matrix = [[1, 2, 3],
    ...           [4, 5, 6],
    ...           [7, 8, 9]]
    >>> for iteration in get_cross_iteration_pattern(len(matrix))
    ...     total = 0
    ...     for indices in iteration:
    ...         total += matrix[indices[0]][indices[1]]
    ...     assert total == 15
    """
    iter_p = []
    # Get first iteration, straight down the middle.
    for i in range(num_iter):
        iter_s = []
        for j in range(num_iter):
            k = j + i
            if k >= num_iter:
                k -= num_iter
            iter_s.append((j, k))
        iter_p.append(iter_s)

    return iter_p


class MaxInt(Infinity, int):
    """An int that will always be greater than another int when compared to
    it."""
    pass


class IncompatibleSpacerError(Exception):
    """Raised when an incompatible spacer is used during some process."""
    pass
