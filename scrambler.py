import random
import math


class LFSR:
    def __init__(self, standard):
        self.seed = []
        self.state = self.seed.copy()
        self.standard = standard
        self.set_standard_parameters()

    def set_standard_parameters(self):
        if self.standard == "TEST":
            self.seed_length = 16
            self.feedback_polynomial = [15, 16]
        elif self.standard == "V34":
            self.seed_length = 23
            self.feedback_polynomial = [18, 23]
        elif self.standard == "DVB":
            self.seed_length = 9
            self.feedback_polynomial = [5, 9]
        elif self.standard == "BLE":
            self.seed_length = 7
            self.feedback_polynomial = [4, 7]

    def shift(self):
        feedback = self.state[self.feedback_polynomial[0] - 1] ^ self.state[self.feedback_polynomial[1] - 1]
        self.state = [feedback] + self.state[:-1]

    def generate(self):
        self.state = self.seed.copy()
        while True:
            self.shift()
            yield self.state[-1]

    def output(self, length):
        generator = self.generate()
        return [next(generator) for _ in range(length)]

    def change_seed(self, new_seed):
        self.seed = new_seed
        self.state = self.seed.copy()


class AdditiveScrambler:
    def __init__(self, lfsr):
        self.lfsr = lfsr

    def scramble(self, data):
        scrambled_data = []
        lfsr_output = self.lfsr.output(len(data))
        for bit, lfsr_bit in zip(data, lfsr_output):
            scrambled_bit = (bit + lfsr_bit) % 2
            scrambled_data.append(scrambled_bit)
        return scrambled_data

    def descramble(self, data):
        descrambled_data = []
        lfsr_output = self.lfsr.output(len(data))
        for bit, lfsr_bit in zip(data, lfsr_output):
            descrambled_bit = (bit + lfsr_bit) % 2
            descrambled_data.append(descrambled_bit)
        return descrambled_data


class MultiplicativeScrambler:
    def __init__(self, lfsr):
        self.lfsr = lfsr

    def scramble(self, data):
        scrambled_data = []
        lfsr_output = self.lfsr.output(len(data))
        for bit, lfsr_bit in zip(data, lfsr_output):
            scrambled_bit = bit ^ lfsr_bit
            scrambled_data.append(scrambled_bit)
        return scrambled_data

    def descramble(self, data):
        descrambled_data = []
        lfsr_output = self.lfsr.output(len(data))
        for bit, lfsr_bit in zip(data, lfsr_output):
            descrambled_bit = bit ^ lfsr_bit
            descrambled_data.append(descrambled_bit)
        return descrambled_data


class Frame:
    def __init__(self, scrambler):
        self.scrambler = scrambler
        self.data = []
        self.descrambled = []

    def generate_data(self, length):
        global loaded_data, stored_data
        if loaded_data:
            print("Use loaded data? [y to confirm]")
            char = input()
            if char == 'y':
                return stored_data
        data = []
        for _ in range(0, length):
            data.append(random.randint(0, 1))
        checkpoints = int(math.sqrt(length))
        all_checks = []
        if checkpoints % 2 == 1:
            checkpoints += 1
        for i in range(0, checkpoints):
            all_checks.append(random.randint(0, length))
        all_checks.sort()
        temp = []
        for j in range(1, len(all_checks), 2):
            if all_checks[j] - all_checks[j - 1] > checkpoints / 2:
                temp.append(all_checks[j])
                temp.append(all_checks[j - 1])
        temp.sort()
        for k in range(0, len(temp), 2):
            random_number = random.randint(0, 1)
            data[temp[k]:temp[k + 1]] = [random_number] * (temp[k + 1] - temp[k])
            # print(f"Start: {temp[k]}, Stop: {temp[k+1]}, Zamiana na: {random_number}")
        return data

    def introduce_noise(self, data, max_same_len, probability, rand_error):
        noise_data = []
        same_len = 0
        last_bit = None
        for bit in data:
            if bit == last_bit:
                same_len += 1
                if same_len >= max_same_len:
                    if random.random() < probability:
                        bit = 1 - bit
                        same_len = 0
            else:
                same_len = 0
            if random.random() < rand_error:
                bit = 1 - bit
            last_bit = bit
            noise_data.append(bit)
        return noise_data

    def find_num_errors(self, original, received):
        return sum(bit1 != bit2 for bit1, bit2 in zip(original, received))

    def generate_frame(self):
        self.generate_lfsr_seed()
        frame_length = random.randint(512, 12144) - self.scrambler.lfsr.seed_length
        frame_length = frame_length - (frame_length % 8)
        return self.scrambler.lfsr.seed + self.generate_data(frame_length)

    def generate_lfsr_seed(self):
        seed_length = self.scrambler.lfsr.seed_length
        new_seed = [random.randint(0, 1) for _ in range(seed_length)]
        while sum(new_seed) == 0:
            new_seed = [random.randint(0, 1) for _ in range(seed_length)]
        self.scrambler.lfsr.change_seed(new_seed)

    def get_frame_length(self):
        return len(self.data)

    def simulate_transmission(self):
        self.data = self.generate_frame()
        print("Original data: ", self.data)

        scrambled = self.scrambler.scramble(self.data)
        print("Scrambled data: ", scrambled)

        noise_no_scrambled = self.introduce_noise(self.data, 5, 0.8, 0.0125)
        noise_scrambled = self.introduce_noise(scrambled, 5, 0.8, 0.0125)

        print("Received data with no scrumble: ", noise_no_scrambled)

        f = open('noscrumble.txt', 'a')
        num_errors = self.find_num_errors(self.data, noise_no_scrambled)
        frame_length = self.get_frame_length()
        output_text = "{}\n".format(num_errors / frame_length)
        f.write(output_text)
        print("Number of errors no scrumble: ", self.find_num_errors(self.data, noise_no_scrambled),
              "with %d bits " % self.get_frame_length())
        self.descrambled = self.scrambler.descramble(noise_scrambled)
        num_errors_scrambled = self.find_num_errors(self.data, self.descrambled)
        frame_length = self.get_frame_length()
        f.close()

        f = open('scrumble.txt', 'a')
        output_text = "{}\n".format(num_errors_scrambled / frame_length)
        f.write(output_text)
        f.close()
        print("Received data with scrumble: ", self.descrambled)
        print("Number of errors scrumble: ", self.find_num_errors(self.data, self.descrambled),
              "with %d bits " % self.get_frame_length())


def test_scrambler(scrambler_type, standard):
    lfsr = LFSR(standard)
    scrambler = scrambler_type(lfsr)
    frame = Frame(scrambler)
    original_data = frame.generate_frame()

    scrambled_data = scrambler.scramble(original_data)
    descrambled_data = scrambler.descramble(scrambled_data)

    assert original_data == descrambled_data, "Test failed: original and descrambled data do not match"
    print("Test passed: original and descrambled data match")


loaded_data = False
stored_data = []


def load_data():
    global loaded_data, stored_data
    try:
        with open('data.txt', 'r') as f:
            dane = f.read().strip()
        # Sprawdzenie, czy dane są w postaci ciągu zer i jedynek
        if all(znak in '01' for znak in dane):
            stored_data = [int(znak) for znak in dane]
            loaded_data = True
            print("Data loaded!")
            return
        else:
            raise ValueError("Dane w pliku nie są w postaci ciągu zer i jedynek.")
    except ValueError as ve:
        print(ve)
        return


def clear_data():
    global loaded_data, stored_data
    loaded_data = False
    stored_data = []
    print("Data cleared!")


def main():
    global scrambler
    print("Choose a scrambler type:")
    print("1. TEST")
    print("2. V34")
    print("3. DVB")
    print("4. BLE")
    standard = input("Enter your standard from given: ")
    lfsr = LFSR(standard)
    state = 1
    while state:
        print("Choose a scrambler type:")
        print("1. Additive Scrambler")
        print("2. Multiplicative Scrambler")
        print("3. Leave program")
        print("4. Start simulation")
        print("5. Test scramblers")
        print("6. Load data")
        print("7. Clear data")
        choice = input("Enter your choice (1/2/3/4/5): ")

        if choice == '1':
            scrambler = AdditiveScrambler(lfsr)
            frame = Frame(scrambler)
            frame.simulate_transmission()
        elif choice == '2':
            scrambler = MultiplicativeScrambler(lfsr)
            frame = Frame(scrambler)
            frame.simulate_transmission()
        elif choice == '3':
            break
        elif choice == '4':
            print("How many simulations?: ")
            loop = int(input())
            f = open('out.txt', 'w')
            f.write('Additive: \n')
            f.close()
            for i in range(0, loop):
                scrambler = AdditiveScrambler(lfsr)
                frame = Frame(scrambler)
                frame.simulate_transmission()
            f = open('out.txt', 'a')
            f.close()
            # f.write('Multiplicative: \n')
            # f.close()
            # for j in range(0, loop):
            #     scrambler = MultiplicativeScrambler(lfsr)
            #     frame = Frame(scrambler)
            #     frame.simulate_transmission()
        elif choice == '5':
            scrambler = AdditiveScrambler(lfsr)
            scrambler = MultiplicativeScrambler(lfsr)
            test_scrambler(AdditiveScrambler, standard)
            test_scrambler(MultiplicativeScrambler, standard)
        elif choice == '6':
            load_data()
        elif choice == '7':
            clear_data()
        else:
            print("Invalid choice. Please choose again.")


if __name__ == "__main__":
    main()
