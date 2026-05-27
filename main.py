def convert_to2(num, width=8):
    result = []

    q = num
    while q != 0:
        q, r = divmod(q, 2)
        result.append(r)

    if len(result) < width:
        zeros = [0] * (width-len(result))
        result.extend(zeros)

    return list(reversed(result))

def convert_to10(bit_list):
    result = 0

    l = len(bit_list)
    for i, item in enumerate(bit_list):
        n = l - 1 - i
        result += item * (1 << n)

    return result

def half_adder(a, b):
    s = a ^ b
    c = a & b
    return s, c

def all_adder(bit_list1, bit_list2, width=8):

    #默认传进来的列表已经是确定的位数了，比如8位
    if len(bit_list1) != width or len(bit_list2) != width:
        return

    result = [0] * width
    i = j = k = width - 1
    
    c = 0
    while k>=0:
        a = bit_list1[i] if i>=0 else 0
        b = bit_list2[j] if j>=0 else 0

        s1, c1 = half_adder(a, b)
        s, c2 = half_adder(s1, c)
        c = c1 | c2
        result[k] = s

        i -= 1
        j -= 1
        k -= 1

    return result

def get_num_neg(bit_list, width=8):
    #按位取反
    neg_bit_list = [1 if bit==0 else 0 for bit in bit_list]
    #再加1
    return all_adder(neg_bit_list, convert_to2(1, width), width)

def add(num1, num2, width=8):
    max_num = convert_to10([1] * width)
    if max(num1, num2) > max_num:
        return
    
    #转换成8位二进制
    bit_list1 = convert_to2(num1, width)
    bit_list2 = convert_to2(num2, width)

    return convert_to10(all_adder(bit_list1, bit_list2))


def sub(num1, num2, width=8):
    max_num = convert_to10([1] * width)
    if max(num1, num2) > max_num:
        return

    #转换成8位二进制
    bit_list1 = convert_to2(num1, width)
    bit_list2 = convert_to2(num2, width)

    neg_ist = get_num_neg(bit_list2, width)

    return convert_to10(all_adder(bit_list1, neg_ist))

def mul(num1, num2, width=8):
    max_num = convert_to10([1] * width)
    if max(num1, num2) > max_num:
        return

    #转换成8位二进制
    bit_list1 = convert_to2(num1, width)
    bit_list2 = convert_to2(num2, width)

    result = convert_to2(0, width)

    for i, bit in enumerate(reversed(bit_list2)):
        if bit==1:
            shifted = bit_list1 + [0] * i
            shifted = shifted[-width:]
            result = all_adder(result, shifted, width)
    return convert_to10(result)

def div(num1, num2, width=8):

    q, r = 0, num1
    while r>=num2:
        r = sub(r, num2, width)
        q += 1

    return q, r

def alu(opt, num1, num2=0, width=8):

    match opt:

        case 'ADD': return add(num1, num2, width)
        case 'SUB': return sub(num1, num2, width)
        case 'MUL': return mul(num1, num2, width)
        case 'DIV': return div(num1, num2, width)
        case 'AND': return num1 & num2
        case 'OR':  return num1 | num2
        case 'XOR': return num1 ^ num2
        case 'NOT': return (~num1) & ((1 << width) - 1)


def get_value(tape, addr, indirect=False):
    if indirect:
        value_addr = tape[abs(addr)]
        return tape[value_addr]
    else:
        return tape[addr]

def set_value(tape, addr, value, indirect=False):
    if indirect:
        value_addr = tape[abs(addr)]
        tape[value_addr] = value
    else:
        tape[addr] = value

def reg(rd, rs1=0, rs2=0):
    return (rd<<6) | (rs1<<4) | (rs2<<2)

def control_unit(program, data, width=8):
    #纸带：程序+数据+栈
    tape = program + data + [0] * 32

    #状态
    PC=0 #程序计数器
    R=[0, 0, 0, 0]  #R1, R2, R3, R4
    SP=len(tape)  #栈指针
    
    

    while True:
        #取指
        opcode = tape[PC]
        addr1 = tape[PC+1]
        addr2 = tape[PC+2]
        addr3 = tape[PC+3]

        reg_field = addr1
        rd = (reg_field >> 6) & 3
        rs1 = (reg_field >> 4) & 3
        rs2 = (reg_field >> 2) & 3
        #执行
        match opcode:
            case 0:  #HALT
                break

            case 1:  #LOAD
                R[rd] = get_value(tape, addr2, indirect=(addr2<0))

            case 2:  #ADD
                R[rd] = alu('ADD', R[rs1], R[rs2], width)

            case 3:  #SUB
                R[rd] = alu('SUB', R[rs1], R[rs2], width)

            case 4:  #STORE
                set_value(tape, addr2, R[rd], indirect=(addr2<0))

            case 5:  #JUMP_IF_ZERO
                if R[rd]==0:
                    PC=addr2
                    continue

            case 6:  #JUMP
                PC=addr2
                continue

            case 7:  #CALL
                SP -= 1
                tape[SP] = PC+4
                PC = addr2
                continue

            case 8:  #RET
                PC = tape[SP]
                SP += 1
                continue

            case 9:  #IN
                value = int(input('输入一个数: '))
                R[rd] = value

            case 10:  #OUT
                print(f'输出: {R[rd]}')

            case 11:  #MUL
                R[rd] = alu('MUL', R[rs1], R[rs2], width)

            case 12:  #DIV
                q, r = alu('DIV', R[rs1], R[rs2], width)
                R[rd] = q

            case 13:  #MOVI
                n = addr2
                R[rd] = n

            case 14:  #MOV
                R[rd] = R[rs1]
        
        PC += 4

    return tape

R0, R1, R2, R3 = 0, 1, 2, 3

def main():

    # 实现 (3 + 5) * 2
    program = [
        13, reg(R1), 3, 0,
        13, reg(R1), 5, 0,
        2, reg(R0, R0, R1), 0, 0,
        13, reg(R1), 2, 0,
        11, reg(R0, R0, R1), 0, 0,
        10, reg(R0), 0, 0,
        0, 0, 0, 0
    ]

    data = []

    tape = control_unit(program, data, 8)

main()