# -*- coding:utf-8 -*-
import unittest
from modian import modian_300_performance_handler
from modian.modian_300_performance_handler import Standing, Seat
from utils.mysql_util import mysql_util


class Modian300Test(unittest.TestCase):

    def setUp(self):
        pass

    def test_draw_tickets_num(self):
        money1 = 10.17
        money2 = 50
        money3 = 100
        money4 = 1017
        money5 = 1

        self.assertEqual(modian_300_performance_handler.get_draw_tickets_num(money1), 1)
        self.assertEqual(modian_300_performance_handler.get_draw_tickets_num(money2), 5)
        self.assertEqual(modian_300_performance_handler.get_draw_tickets_num(money3), 10)
        self.assertEqual(modian_300_performance_handler.get_draw_tickets_num(money4), 10)
        self.assertEqual(modian_300_performance_handler.get_draw_tickets_num(money5), 0)

    def test_can_draw_tickets(self):
        for i in range(10):
            print(modian_300_performance_handler.can_draw_tickets())

    def test_convert_number_to_seats(self):
        number1 = 1
        number2 = 38
        number3 = 300
        number4 = 90
        number5 = 228

        self.assertEqual(modian_300_performance_handler.convert_number_to_seats(number1).row, 1)
        self.assertEqual(modian_300_performance_handler.convert_number_to_seats(number1).col, 1)

        self.assertEqual(modian_300_performance_handler.convert_number_to_seats(number2).row, 2)
        self.assertEqual(modian_300_performance_handler.convert_number_to_seats(number2).col, 8)

        self.assertEqual(modian_300_performance_handler.convert_number_to_seats(number3).row, 10)
        self.assertEqual(modian_300_performance_handler.convert_number_to_seats(number3).col, 30)

        self.assertEqual(modian_300_performance_handler.convert_number_to_seats(number4).row, 3)
        self.assertEqual(modian_300_performance_handler.convert_number_to_seats(number4).col, 30)

        self.assertEqual(modian_300_performance_handler.convert_number_to_seats(number5).row, 8)
        self.assertEqual(modian_300_performance_handler.convert_number_to_seats(number5).col, 18)

    def test_draw_tickets(self):
        import random
        self.current_available_seats = modian_300_performance_handler.get_current_available_seats()
        for i in range(50):
            self.abc(random.randint(1, 300), random.randint(1, 1000))

    def abc(self, backer_money, user_id):
        print('backer_money: %s, user_id: %s' % (backer_money, user_id))
        seats = []
        standings = []
        ticket_num = modian_300_performance_handler.get_draw_tickets_num(backer_money)
        for i in range(ticket_num):
            if len(self.current_available_seats) > 0:
                seat_number = modian_300_performance_handler.draw_tickets(self.current_available_seats)
                if seat_number != -1:
                    self.current_available_seats.remove(seat_number)
                    mysql_util.query("""
                                        INSERT INTO `seats_record` (`seats_type`, `modian_id`, `seats_number`) VALUES
                                            (%s, %s, %s)
                                    """, (1, user_id, seat_number))
                    seats.append(seat_number)
            else:
                standing_number = modian_300_performance_handler.draw_standing_tickets()
                if standing_number != -1:
                    mysql_util.query("""
                                    INSERT INTO `seats_record` (`seats_type`, `modian_id`, `seats_number`) VALUES
                                        (%s, %s, %s)
                                """, (2, user_id, standing_number))
                    standings.append(Standing(standing_number))

        if len(seats) == 0 and len(standings) == 0:
            report_message = '抱歉，本次抽选未中T_T\n'
        else:
            report_message = '您参与的FXF48公演抽选成功！\n'
            idx = 1
            if len(seats) > 0:
                for seat in seats:
                    # seat_o = modian_300_performance_handler.convert_number_to_seats(seat)
                    seat_o = modian_300_performance_handler.seat_number_to_date_dict[seat]
                    report_message += '%d. 公演日期: %d年%d月%d日, 座位号: %s排%s号' % (
                        idx, seat_o.year, seat_o.month, seat_o.day, seat_o.row, seat_o.col)
                    # 特殊座位
                    if seat in modian_300_performance_handler.special_seats_wording.keys():
                        report_message += ', %s' % modian_300_performance_handler.special_seats_wording[seat]
                    report_message += '\n'
                    idx += 1
            if len(standings) > 0:
                for standing in standings:
                    report_message += '%d. 座位号: 加站%03d\n' % (idx, standing.number)
                    idx += 1
            report_message += '\n'
        print(report_message)


if __name__ == '__main__':
    unittest.main()
