// creation table
let parkings = ["A01", "A02", "A03", "A04", "A05", "A06", "A07", "A08", "A09", "A10", "A12", "A14", "A16", "A18", "A30", "A32", "A34", "A36", "A38", "AT1", "AT2", "AT3", "AT4", "AT5", "AT6", "AT7",
    "AT8", "AT9", "B01", "B02", "B03", "B04", "B05", "B06", "B07", "B08", "B09", "B10", "B11", "B12", "B13", "B14", "B15", "B16", "B18", "B20", "C02", "C03", "C04", "C05", "C06", "C07",
    "C08", "C10", "C12", "C14", "C4A", "CF9", "CFE", "CFW", "D02", "D03", "D04", "D05", "D06", "D07", "D08", "D09", "D10", "D11", "D12", "D13", "D14", "D15", "D16", "D17", "D18", "D19",
    "D20", "D22", "D24", "G10", "G11", "G12", "G13", "G14", "G20", "G21", "G22", "G23", "G24", "G29", "G30", "G31", "G32", "G33", "G35", "H01", "H02", "H03", "H04", "H05", "H06", "H07", "H08", "H09", "H10", "H11", "H12", "H20", "H21", "H22", "H23", "H30", "H34", "H40", "H50", "H55", "H60", "H65", "H70", "H80", "H87"
];


function hourToSlot(hour) {
    let t = hour.split(" ")[1].split(':');
    let tt = Number(t[0]) * 12 + Number(t[1]) / 5;
    return tt;
}

function affectation(parking, departure, arrival, nbslots, color, plane, numplane, reward, cie) {
    let first = hourToSlot(arrival) + 2; // 1 is th 2 is the first
    let hd = departure.split(" ")[1];
    let ha = arrival.split(" ")[1];
    //console.log("p=", parking, "h=", hour, "nb=", nbslots, reward);
    color = "rgba(" + color + "," + (Number(reward) / 100.) + ")";
    let tr = $("#table tr:nth-child(" + parking + ")");
    tr.children().each(function (i) {
        if (i < first || i > first + Number(nbslots))
            return;
        let td = $(this);
        if (td.attr('affected') != undefined) {
            color = "red";
            $('body').append("Probl&eacute;me vol " + numplane + " " + td.attr('affected') + "<br >");
        }
        td.css('background-color', color);
        td.css("border-top", "1px solid black");
        td.css("border-bottom", "1px solid black");
        td.attr("affected", numplane);
        td.attr("title", "num=" + numplane + " cie=" + cie +" hours=(" +ha +"->" +hd+ ") plane=" + plane + " reward=" + reward);
    });

    $("#table tr:nth-child(" + parking  + ") td:nth-child(" + (first+1)+")").css("border-left", "1px solid black");
    $("#table tr:nth-child(" + parking  + ") td:nth-child(" + (first+Number(nbslots)+2)+")").css("border-left", "1px solid black");

}


function table() {
    let table = $('#table');
    for (p = 0; p < parkings.length; p++) {
        let tr = $('<tr><th>' + parkings[p] + '</th>');
        let tmp = "";
        for (let i = 0; i < 288; i++)
            tmp = tmp + "<td></td>";
        //
        // tr.append('<td></td>');
        tr.append(tmp);
        table.append(tr);
    }
}

$(document).ready(function () {

    table();

    for(let i = 0; i < flights.length; i++) {
        let f = flights[i];
        affectation(
            parkings.indexOf(f.parking) + 1, f.departure, f.arrival, f.n5,
            "0,0,255", f.plane, f.index, f.reward, f.company);
    }

});
